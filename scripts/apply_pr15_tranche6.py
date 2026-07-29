from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"{label}: expected one anchor, found {text.count(old)}")
    return text.replace(old, new, 1)


# media.voice
path = Path("backend/media/voice.py")
text = path.read_text()
text = replace_once(
    text,
    "from core.ai_egress import AUDIO, assert_ai_egress_allowed\n",
    "from core.ai_egress import AUDIO, AIEgressDenied\n"
    "from core.ai_processor_policy import AIProcessorPolicyDenied\n"
    "from llm.errors import LLMProviderError\n"
    "from llm.runtime import execute_external_provider_call\n",
    "voice imports",
)
text = replace_once(
    text,
    "        assert_ai_egress_allowed(AUDIO)\n        from google import genai\n",
    "        from google import genai\n",
    "voice assertion",
)
old = '''        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": audio_b64,
                            }
                        },
                        {"text": user_prompt},
                    ]
                }
            ],
            config={
                "system_instruction": _STT_SYSTEM,
                "temperature": 0.0,   # deterministic transcription
            },
        )
'''
new = '''        response = execute_external_provider_call(
            "gemini",
            AUDIO,
            "transcribe",
            lambda: client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    {
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": audio_b64,
                                }
                            },
                            {"text": user_prompt},
                        ]
                    }
                ],
                config={
                    "system_instruction": _STT_SYSTEM,
                    "temperature": 0.0,
                },
            ),
        )
'''
text = replace_once(text, old, new, "voice provider call")
text = replace_once(
    text,
    "    except Exception as exc:\n        logger.exception(\"STT: Gemini transcription failed (lang=%s)\", language)\n        raise TranscriptionError(f\"Gemini STT error: {exc}\") from exc\n",
    "    except (AIEgressDenied, AIProcessorPolicyDenied, LLMProviderError):\n"
    "        raise\n"
    "    except Exception:\n"
    "        logger.exception(\"STT: transcription failed (lang=%s)\", language)\n"
    "        raise TranscriptionError(\"STT request could not be completed safely.\") from None\n",
    "voice exceptions",
)
path.write_text(text)


# media.vision
path = Path("backend/media/vision.py")
text = path.read_text()
text = replace_once(
    text,
    "from core.ai_egress import IMAGE, assert_ai_egress_allowed\n",
    "from core.ai_egress import IMAGE, AIEgressDenied\n"
    "from core.ai_processor_policy import AIProcessorPolicyDenied\n"
    "from llm.runtime import execute_external_provider_call\n",
    "vision imports",
)
text = text.replace("        assert_ai_egress_allowed(IMAGE)\n", "")
text = replace_once(
    text,
    '''        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=genai_types.GenerateContentConfig(
                system_instruction=_MEAL_SYSTEM,
                temperature=0.1,
            ),
        )
''',
    '''        response = execute_external_provider_call(
            "gemini",
            IMAGE,
            "meal_vision",
            lambda: client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=genai_types.GenerateContentConfig(
                    system_instruction=_MEAL_SYSTEM,
                    temperature=0.1,
                ),
            ),
        )
''',
    "meal vision call",
)
text = replace_once(
    text,
    "    except json.JSONDecodeError:\n",
    "    except (AIEgressDenied, AIProcessorPolicyDenied):\n        raise\n\n    except json.JSONDecodeError:\n",
    "meal policy exceptions",
)
text = replace_once(
    text,
    '''        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=genai_types.GenerateContentConfig(
                system_instruction=_GLUCO_SYSTEM,
                temperature=0.0,
            ),
        )
''',
    '''        response = execute_external_provider_call(
            "gemini",
            IMAGE,
            "glucometer_ocr",
            lambda: client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=genai_types.GenerateContentConfig(
                    system_instruction=_GLUCO_SYSTEM,
                    temperature=0.0,
                ),
            ),
        )
''',
    "glucometer vision call",
)
text = replace_once(
    text,
    "    except (json.JSONDecodeError, KeyError, ValueError):\n",
    "    except (AIEgressDenied, AIProcessorPolicyDenied):\n        raise\n\n    except (json.JSONDecodeError, KeyError, ValueError):\n",
    "glucometer policy exceptions",
)
path.write_text(text)


# document image extractor
path = Path("backend/diabetes/services/documents/extractors/image.py")
text = path.read_text()
text = replace_once(
    text,
    "from core.ai_egress import IMAGE, assert_ai_egress_allowed\n",
    "from core.ai_egress import IMAGE, AIEgressDenied\n"
    "from core.ai_processor_policy import AIProcessorPolicyDenied\n"
    "from llm.runtime import execute_external_provider_call\n",
    "document image imports",
)
text = replace_once(
    text,
    "        assert_ai_egress_allowed(IMAGE)\n        import os\n",
    "        import os\n",
    "document image assertion",
)
text = replace_once(
    text,
    '''        response = model.generate_content(
            contents=[
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": b64,
                            }
                        },
                        {
                            "text": (
                                "Transcribe ALL visible text from this image exactly as written. "
                                "Include numbers, dates, units, labels, and table content. "
                                "Preserve the structure with newlines. "
                                "Do NOT interpret or summarise — only transcribe. "
                                "Return plain text only."
                            )
                        },
                    ]
                }
            ]
        )
''',
    '''        response = execute_external_provider_call(
            "gemini",
            IMAGE,
            "document_image_ocr",
            lambda: model.generate_content(
                contents=[
                    {
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": b64,
                                }
                            },
                            {
                                "text": (
                                    "Transcribe ALL visible text from this image exactly as written. "
                                    "Include numbers, dates, units, labels, and table content. "
                                    "Preserve the structure with newlines. "
                                    "Do NOT interpret or summarise — only transcribe. "
                                    "Return plain text only."
                                )
                            },
                        ]
                    }
                ]
            ),
        )
''',
    "document image call",
)
text = replace_once(
    text,
    "    except KeyError:\n",
    "    except (AIEgressDenied, AIProcessorPolicyDenied):\n        raise\n\n    except KeyError:\n",
    "document image policy exceptions",
)
path.write_text(text)


# processor registry: declare actual Gemini modalities/purposes while retaining PENDING status.
path = Path("backend/core/ai_processor_policy.py")
text = path.read_text()
text = replace_once(
    text,
    "_ALL_TEXT_PURPOSES = frozenset(\n",
    "_ALL_TEXT_PURPOSES = frozenset(\n",
    "processor purpose anchor",
)
text = replace_once(
    text,
    '''            allowed_modalities=frozenset({"text"}),
            allowed_purposes=_ALL_TEXT_PURPOSES,
            status=PENDING,
''',
    '''            allowed_modalities=frozenset({"text", "audio", "image"}),
            allowed_purposes=_ALL_TEXT_PURPOSES
            | frozenset({"voice_transcription", "meal_vision", "glucometer_ocr"}),
            status=PENDING,
''',
    "gemini modalities",
)
path.write_text(text)


# Existing STT unit tests isolate provider governance from SDK-shape tests.
path = Path("backend/diabetes/tests/test_sprint4_services.py")
text = path.read_text()
text = replace_once(
    text,
    '''        self._egress_patcher = patch("media.voice.assert_ai_egress_allowed")
        self._egress_patcher.start()
        self.addCleanup(self._egress_patcher.stop)
''',
    '''        self._runtime_patcher = patch(
            "media.voice.execute_external_provider_call",
            side_effect=lambda provider, modality, operation, call: call(),
        )
        self._runtime_patcher.start()
        self.addCleanup(self._runtime_patcher.stop)
''',
    "STT test runtime patch",
)
path.write_text(text)
