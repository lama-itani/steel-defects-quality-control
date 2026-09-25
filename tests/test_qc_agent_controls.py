import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, mock_open, patch

from src import qc_agent as agent


INSPECTION = {
    "inspection_id": "a" * 32,
    "status": "completed",
    "findings": [{"class_name": "Scratches"}],
}


def tool_response(name, arguments, count=1):
    calls = [
        SimpleNamespace(
            id=f"call_{i}",
            type="function",
            function=SimpleNamespace(
                name=name,
                arguments=json.dumps(arguments),
            ),
        )
        for i in range(count)
    ]
    message = MagicMock()
    message.tool_calls = calls
    message.model_dump.return_value = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                },
            }
            for call in calls
        ],
    }
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message, finish_reason="tool_calls")]
    )


def final_response():
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    tool_calls=None,
                    content="Draft for human review.",
                ),
                finish_reason="stop",
            )
        ]
    )


class AgentControls(unittest.TestCase):
    def run_mocked(self, responses, dispatcher):
        client = MagicMock()
        client.chat.completions.create.side_effect = responses

        with (
            patch.object(agent, "OpenAI") as factory,
            patch(
                "builtins.open",
                mock_open(read_data='{"access_token": "test-only"}'),
            ),
            patch.object(agent, "dispatch_tool", dispatcher),
        ):
            factory.return_value.__enter__.return_value = client
            result = agent.run_agent("Retrieve the saved inspection.")

        self.assertEqual(result["report_status"], "draft_for_human_review")
        return result

    def test_dispatch_rejects_invalid_requests(self):
        function = MagicMock()
        invalid = [
            ("unknown_tool", "{}"),
            ("get_inspection", {}),
            ("get_inspection", "{"),
            ("get_inspection", "[]"),
            ("get_inspection", "{}"),
            ("get_inspection", '{"inspection_id": 123}'),
            ("get_inspection", '{"inspection_id": null}'),
            ("get_inspection", '{"wrong_key": "abc"}'),
            (
                "get_inspection",
                '{"inspection_id": "abc", "extra": "value"}',
            ),
        ]
        with patch.dict(
            agent.REGISTRY,
            {"get_inspection": (function, "inspection_id")},
            clear=True,
        ):
            for name, arguments in invalid:
                with self.subTest(name=name, arguments=arguments):
                    with self.assertRaises(ValueError):
                        agent.dispatch_tool(name, arguments)

        function.assert_not_called()

    def test_fifth_call_is_not_executed(self):
        dispatcher = MagicMock(return_value=INSPECTION)
        responses = [
            tool_response("get_inspection", {"inspection_id": "a" * 32})
            for _ in range(5)
        ]
        result = self.run_mocked(responses, dispatcher)

        self.assertEqual(result["status"], "tool_limit")
        self.assertEqual(result["tool_calls_used"], 4)
        self.assertEqual(dispatcher.call_count, 4)
        self.assertEqual(len(result["tool_results"]), 4)

    def test_oversized_batch_executes_nothing(self):
        dispatcher = MagicMock()
        result = self.run_mocked(
            [tool_response(
                "get_inspection", {"inspection_id": "a" * 32}, count=5
            )],
            dispatcher,
        )

        self.assertEqual(result["status"], "tool_limit")
        self.assertEqual(result["tool_calls_used"], 0)
        dispatcher.assert_not_called()

    def test_unrelated_guidance_rejected_before_dispatch(self):
        dispatcher = MagicMock(return_value=INSPECTION)
        result = self.run_mocked(
            [
                tool_response(
                    "get_inspection", {"inspection_id": "a" * 32}
                ),
                tool_response(
                    "lookup_defect_guidance", {"defect_class": "Patches"}
                ),
                final_response(),
            ],
            dispatcher,
        )

        self.assertEqual(dispatcher.call_count, 1)
        self.assertEqual(
            dispatcher.call_args.args[0], "get_inspection"
        )
        self.assertEqual(result["tool_calls_used"], 2)
        rejected = result["tool_results"][1]
        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["allowed_guidance_classes"], ["Scratches"])

    def test_llm_failure_preserves_evidence_and_hides_details(self):
        dispatcher = MagicMock(return_value=INSPECTION)
        result = self.run_mocked(
            [
                tool_response(
                    "get_inspection", {"inspection_id": "a" * 32}
                ),
                RuntimeError("SECRET_RAW_ERROR_SENTINEL"),
            ],
            dispatcher,
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["tool_calls_used"], 1)
        self.assertTrue(result["tool_results"][0]["ok"])
        self.assertEqual(
            result["tool_results"][0]["result"], INSPECTION
        )
        self.assertNotIn("SECRET_RAW_ERROR_SENTINEL", json.dumps(result))


if __name__ == "__main__":
    unittest.main()