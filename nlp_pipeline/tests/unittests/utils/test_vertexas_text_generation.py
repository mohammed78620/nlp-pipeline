from nlp_pipeline.settings import BOL_PE_GCP_LOCATION, BOL_PE_HYPERPARAMETERS, BOL_PE_LLM_MODEL, GOOGLE_PROJECT_ID
from nlp_pipeline.utils.vertexai_text_generation import LLMPrediction


class TestLLMPrediction:
    def test__init__(self):
        llm = LLMPrediction(GOOGLE_PROJECT_ID, BOL_PE_GCP_LOCATION, BOL_PE_LLM_MODEL, BOL_PE_HYPERPARAMETERS)
        assert llm is not None

    def test_text_prediction(self):
        prompt = "what's the meaning of life?"
        llm = LLMPrediction(GOOGLE_PROJECT_ID, BOL_PE_GCP_LOCATION, BOL_PE_LLM_MODEL, BOL_PE_HYPERPARAMETERS)

        result = llm.text_prediction(prompt)

        assert result is not None
        assert llm.is_good_result(result) is True

        result_text = llm.get_result_text(result)
        assert result_text is not None
        assert type(result_text) is str
        assert len(result_text) > 0
