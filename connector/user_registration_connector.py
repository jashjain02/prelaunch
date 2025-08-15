from models.crude_operations_model import CrudeOperationsModel
from models.user_registration_model import UserRegistrationModel

class UserRegistrationConnector(CrudeOperationsModel[UserRegistrationModel, None, None]):
    pass

user_registration_connector = UserRegistrationConnector(UserRegistrationModel)
