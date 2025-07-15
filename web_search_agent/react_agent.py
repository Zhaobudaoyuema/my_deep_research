import json
from abc import ABC
from typing import Optional, List, Union, Any

from pydantic import BaseModel, Field

from web_search_agent.llm import LLM
from web_search_agent.prompt.toolcall import SYSTEM_PROMPT, NEXT_STEP_PROMPT
from web_search_agent.schema import Message, ToolCall, ToolChoice, Memory, TOOL_CHOICE_TYPE, ROLE_TYPE, AgentState
from web_search_agent.tools.ask_human import AskHuman
from web_search_agent.tools.create_chat_completion import CreateChatCompletion
from web_search_agent.tools.python_execute import PythonExecute
from web_search_agent.tools.terminate import Terminate
from web_search_agent.tools.tool_collection import ToolCollection
from web_search_agent.tools.web_search import WebSearch

TOOL_CALL_REQUIRED = "Tool calls required but none provided"

class ReActAgent(BaseModel, ABC):
    name: str = Field(default="BaseAgent", description="Unique name of the agent")

    llm: LLM = Field(default_factory=LLM, description="Language model instance")

    max_steps: int = Field(default=20, description="Maximum steps before termination")
    current_step: int = Field(default=0, description="Current step in execution")

    system_prompt: str = SYSTEM_PROMPT
    next_step_prompt: str = NEXT_STEP_PROMPT

    available_tools: ToolCollection = ToolCollection(
        WebSearch(), Terminate(), CreateChatCompletion(),
    )

    tool_calls: List[ToolCall] = Field(default_factory=list)
    tool_choices: TOOL_CHOICE_TYPE = ToolChoice.AUTO

    memory: Memory = Field(default_factory=Memory)

    max_observe: Optional[Union[int, bool]] = None

    state: AgentState = Field(
        default=AgentState.IDLE, description="Current agent state"
    )

    special_tool_names: List[str] = Field(default_factory=lambda: [Terminate().name])

    async def run(self, request: Optional[str] = None) -> str:
        if request:
            self.update_memory("user", request)

            while self.current_step < self.max_steps and self.state != AgentState.FINISHED:
                self.current_step += 1
                print(f"Executing step {self.current_step}/{self.max_steps}")
                should_act = await self.think()
                if not should_act:
                    return "Thinking complete - no action needed"
                await self.act()

    async def think(self) -> bool:
        if self.next_step_prompt:
            user_msg = Message.user_message(self.next_step_prompt)
            self.messages += [user_msg]

        try:

            # Get response with tool options
            response = await self.llm.ask_tool(
                messages=self.messages,
                system_msgs=(
                    [Message.system_message(self.system_prompt)]
                    if self.system_prompt
                    else None
                ),
                tools=self.available_tools.to_params(),
                tool_choice=self.tool_choices,
            )
            self.tool_calls = tool_calls = (
                response.tool_calls if response and response.tool_calls else []
            )
            content = response.content if response and response.content else ""

            print(f"✨ {self.name}'s thoughts: {content}")
            print(
                f"🛠️ {self.name} selected {len(tool_calls) if tool_calls else 0} tools to use"
            )
            if tool_calls:
                print(
                    f"🧰 Tools being prepared: {[call.function.name for call in tool_calls]}"
                )
                print(f"🔧 Tool arguments: {tool_calls[0].function.arguments}")
        except ValueError:
            raise

        try:
            if response is None:
                raise RuntimeError("No response received from the LLM")

            # Handle different tool_choices modes
            if self.tool_choices == ToolChoice.NONE:
                if tool_calls:
                    print(
                        f"🤔 Hmm, {self.name} tried to use tools when they weren't available!"
                    )
                if content:
                    self.memory.add_message(Message.assistant_message(content))
                    return True
                return False

            # Create and add assistant message
            assistant_msg = (
                Message.from_tool_calls(content=content, tool_calls=self.tool_calls)
                if self.tool_calls
                else Message.assistant_message(content)
            )
            self.memory.add_message(assistant_msg)

            if self.tool_choices == ToolChoice.REQUIRED and not self.tool_calls:
                return True  # Will be handled in act()

            # For 'auto' mode, continue with content if no commands but content exists
            if self.tool_choices == ToolChoice.AUTO and not self.tool_calls:
                return bool(content)

            return bool(self.tool_calls)
        except Exception as e:
            print(f"🚨 Oops! The {self.name}'s thinking process hit a snag: {e}")
            self.memory.add_message(
                Message.assistant_message(
                    f"Error encountered while processing: {str(e)}"
                )
            )
            return False

    async def act(self) -> str:
        if not self.tool_calls:
            if self.tool_choices == ToolChoice.REQUIRED:
                raise ValueError(TOOL_CALL_REQUIRED)

            # Return last message content if no tool calls
            return self.messages[-1].content or "No content or commands to execute"

        results = []
        for command in self.tool_calls:
            # Reset base64_image for each tool call

            result = await self.execute_tool(command)

            print(
                f"🎯 Tool '{command.function.name}' completed its mission! Result: {result}"
            )

            # Add tool response to memory
            tool_msg = Message.tool_message(
                content=result,
                tool_call_id=command.id,
                name=command.function.name,
            )
            self.memory.add_message(tool_msg)
            results.append(result)

        return "\n\n".join(results)

    async def execute_tool(self, command: ToolCall) -> str:
        """Execute a single tool call with robust error handling"""
        if not command or not command.function or not command.function.name:
            return "Error: Invalid command format"

        name = command.function.name
        if name not in self.available_tools.tool_map:
            return f"Error: Unknown tool '{name}'"

        try:
            # Parse arguments
            args = json.loads(command.function.arguments or "{}")

            # Execute the tool
            print(f"🔧 Activating tool: '{name}'...")
            result = await self.available_tools.execute(name=name, tool_input=args)

            await self._handle_special_tool(name=name, result=result)

            # Format result for display (standard case)
            observation = (
                f"Observed output of cmd `{name}` executed:\n{str(result)}"
                if result
                else f"Cmd `{name}` completed with no output"
            )

            return observation
        except json.JSONDecodeError:
            error_msg = f"Error parsing arguments for {name}: Invalid JSON format"
            print(
                f"📝 Oops! The arguments for '{name}' don't make sense - invalid JSON, arguments:{command.function.arguments}"
            )
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"⚠️ Tool '{name}' encountered a problem: {str(e)}"
            print(error_msg)
            return f"Error: {error_msg}"



    @property
    def messages(self) -> List[Message]:
        """Retrieve a list of messages from the agent's memory."""
        return self.memory.messages

    @messages.setter
    def messages(self, value: List[Message]):
        """Set the list of messages in the agent's memory."""
        self.memory.messages = value

    def update_memory(
        self,
        role: ROLE_TYPE,  # type: ignore
        content: str,
        base64_image: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Add a message to the agent's memory.

        Args:
            role: The role of the message sender (user, system, assistant, tool).
            content: The message content.
            base64_image: Optional base64 encoded image.
            **kwargs: Additional arguments (e.g., tool_call_id for tool messages).

        Raises:
            ValueError: If the role is unsupported.
        """
        message_map = {
            "user": Message.user_message,
            "system": Message.system_message,
            "assistant": Message.assistant_message,
            "tool": lambda content, **kw: Message.tool_message(content, **kw),
        }

        if role not in message_map:
            raise ValueError(f"Unsupported message role: {role}")

        # Create message with appropriate parameters based on role
        kwargs = {"base64_image": base64_image, **(kwargs if role == "tool" else {})}
        self.memory.add_message(message_map[role](content, **kwargs))

    def _is_special_tool(self, name: str) -> bool:
        """Check if tool name is in special tools list"""
        return name.lower() in [n.lower() for n in self.special_tool_names]

    async def _handle_special_tool(self, name: str, result: Any, **kwargs):
        """Handle special tool execution and state changes"""
        if not self._is_special_tool(name):
            return

        if self._should_finish_execution(name=name, result=result, **kwargs):
            # Set agent state to finished
            print(f"🏁 Special tool '{name}' has completed the task!")
            self.state = AgentState.FINISHED

    def _should_finish_execution(self, name: str, **kwargs) -> bool:
        """Determine if tool execution should finish the agent"""
        # Terminate if the tool name is 'terminate'
        return name.lower() == "terminate"