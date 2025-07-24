from models.agent_tokens_model import AgentTokenModel
from models.crude_operations_model import CrudeOperationsModel

class AgentTokenConnector(CrudeOperationsModel[AgentTokenModel, None, None]):
    pass

agent_token_connector = AgentTokenConnector(AgentTokenModel) 