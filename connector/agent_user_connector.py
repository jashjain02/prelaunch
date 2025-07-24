from models.agent_user_model import AgentUserModel
from models.crude_operations_model import CrudeOperationsModel

class AgentUserConnector(CrudeOperationsModel[AgentUserModel, None, None]):
    pass

agent_user_connector = AgentUserConnector(AgentUserModel) 