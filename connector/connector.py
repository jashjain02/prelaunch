from models.crude_operations_model import CrudeOperationsModel
from models.event_registration_model import EventRegistrationModel
from models.transaction_model import TransactionModel


class EventRegistrationConnector(CrudeOperationsModel[EventRegistrationModel, None, None]):
    pass

class TransactionConnector(CrudeOperationsModel[TransactionModel, None, None]):
    pass

event_registration_connector = EventRegistrationConnector(EventRegistrationModel)
transaction_connector = TransactionConnector(TransactionModel)