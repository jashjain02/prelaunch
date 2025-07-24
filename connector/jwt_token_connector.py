from models.jwt_token_model import JwtTokenModel
from models.crude_operations_model import CrudeOperationsModel
from schemas.jwt_token_schema import JwtTokenSchema

class JwtTokenConnector(CrudeOperationsModel[JwtTokenModel, JwtTokenSchema, None]):
    pass

jwt_token_connector = JwtTokenConnector(JwtTokenModel) 