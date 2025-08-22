from models.crude_operations_model import CrudeOperationsModel
from models.event_registration_model import EventRegistrationModel
from models.transaction_model import TransactionModel
from models.user_registration_model import UserRegistrationModel
from models.sports_model import SportsModel
from models.jindal_registration_model import JindalRegistrationModel
from models.orangetheory_registration_model import OrangetheoryRegistrationModel


class EventRegistrationConnector(CrudeOperationsModel[EventRegistrationModel, None, None]):
    pass

class TransactionConnector(CrudeOperationsModel[TransactionModel, None, None]):
    pass

class UserRegistrationConnector(CrudeOperationsModel[UserRegistrationModel, None, None]):
    pass

class SportsConnector(CrudeOperationsModel[SportsModel, None, None]):
    pass

class JindalRegistrationConnector(CrudeOperationsModel[JindalRegistrationModel, None, None]):
    pass

class OrangetheoryRegistrationConnector(CrudeOperationsModel[OrangetheoryRegistrationModel, None, None]):
    pass

event_registration_connector = EventRegistrationConnector(EventRegistrationModel)
transaction_connector = TransactionConnector(TransactionModel)
user_registration_connector = UserRegistrationConnector(UserRegistrationModel)
sports_connector = SportsConnector(SportsModel)
jindal_registration_connector = JindalRegistrationConnector(JindalRegistrationModel)
orangetheory_registration_connector = OrangetheoryRegistrationConnector(OrangetheoryRegistrationModel)