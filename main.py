from app.renderer import render
from app.transformer import DataTransformer

transformer = DataTransformer()
transformer.make_flow()
transformer.parse_applications()

render(transformer)
