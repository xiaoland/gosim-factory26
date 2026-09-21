import unittest

from scripts.responses_compat import sanitize_responses_input


class ResponsesCompatTests(unittest.TestCase):
    def test_removes_only_exact_empty_input_text_and_empty_message(self):
        request = {
            "input": [
                {"type": "function_call", "call_id": "call-1", "name": "view_image", "arguments": "{}"},
                {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": ""}]},
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {"type": "output_text", "text": ""},
                        {"type": "input_image", "image_url": "data:image/png;base64,x"},
                    ],
                },
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "  "}],
                },
                {"type": "function_call_output", "call_id": "call-1", "output": ""},
            ],
            "messages": [{"role": "assistant", "content": [{"type": "text", "text": ""}]}],
        }

        cleaned = sanitize_responses_input(request)

        self.assertEqual([item["type"] for item in cleaned["input"]], ["function_call", "message", "message", "function_call_output"])
        self.assertEqual(cleaned["input"][1]["content"][0]["type"], "input_image")
        self.assertEqual(cleaned["input"][2]["content"][0]["text"], "  ")
        self.assertEqual(cleaned["input"][3]["output"], "")
        self.assertEqual(cleaned["messages"], request["messages"])

    def test_preserves_other_blocks_invalid_values_and_does_not_mutate_input(self):
        request = {
            "input": [
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": None},
                        {"type": "text", "text": 0},
                        {"type": "custom", "text": ""},
                        {"type": "input_image", "image_url": "x"},
                    ],
                }
            ]
        }

        cleaned = sanitize_responses_input(request)

        self.assertEqual(cleaned, request)
        self.assertIsNot(cleaned, request)
        self.assertIsNot(cleaned["input"], request["input"])


if __name__ == "__main__":
    unittest.main()
