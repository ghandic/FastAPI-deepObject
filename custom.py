from typing import Any, Callable, Dict, List, Optional, _GenericAlias, Union
from inspect import signature, Signature, Parameter
from collections import Counter

from pydantic import BaseModel, ValidationError
from fastapi import Query, Depends, HTTPException


def flatten_dict(data: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    """To go from {"role": ["Admin", "Developer"], "first_name": ["Andy"]} -> [{"role": "Admin", "first_name": "Andy"}, {"role": "Developer", "first_name": None}]"""
    flattened = []
    for i in range(max(len(v) if v else 0 for v in data.values())):
        remapped = {}
        for k in data:
            val = data.get(k, [None])[i : i + 1]
            if val:
                remapped[k] = val[0]
        flattened.append(remapped)
    return flattened


def get_settings(model: BaseModel, name: str) -> Dict[str, Any]:
    if hasattr(model, "Config") and hasattr(model.Config, "deep_query"):
        return model.Config.deep_query.get(name, {})
    return {}


def DeepQuery(model: Union[_GenericAlias, BaseModel], name: str = "", unique_on: List[str] = []) -> Depends:
    # Handing typing.List
    is_list = False
    is_optional = False

    if hasattr(model, "__origin__"):
        if model.__origin__ == list:
            is_list = True
            if len(model.__args__) != 1:
                raise TypeError("Can only have a single BaseModel type in the List")
        elif model.__origin__ == Union and model.__args__[1] == type(None):
            is_optional = True
            if len(model.__args__) != 2:
                raise TypeError("Can only have a Optional[BaseModel] (which is a Union[BaseModel, NoneType]")
        else:
            raise TypeError("Can only have Optional[BaseModel] or List[BaseModel]")

        model = model.__args__[0]

    if not issubclass(model, BaseModel):
        raise TypeError("Must be a subclass of BaseModel")
    # Override the name of the parameter displayed in FastAPI - defaults to the lowercase name of the Pydantic model
    if not name:
        name = model.__name__.lower()

    # Dummy function with functionality - signature to be replaced in next step
    if is_list:

        async def parse(**kwargs) -> List[model]:
            flat_kwargs = flatten_dict(kwargs)
            if unique_on:
                for unique_key in unique_on:
                    vals = list(map(lambda kwargs: kwargs.get(unique_key), flat_kwargs))
                    if len(set(vals)) != len(vals):
                        raise HTTPException(
                            status_code=400, detail=f"Duplicate query parameters supplied for {unique_key}"
                        )
            try:
                return [model(**kwarg) for kwarg in flat_kwargs]
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"{e}")

    else:

        async def parse(**kwargs) -> model:
            try:
                if is_optional:
                    if any(v is not None for v in kwargs.values()):
                        return model(**kwargs)
                    return None

                return model(**kwargs)
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"{e}")

    def get_default(param: Parameter):
        if is_optional or is_list:
            return None
        return ... if (param.default is Parameter.empty) else param.default

    # TODO: Support nested objects eg role[sub][name]=xxx
    sig = signature(model)

    newsig = Signature(
        parameters=[
            Parameter(
                name=param.name,
                default=Query(get_default(param), alias=f"{name}[{param.name}]", **get_settings(model, param.name),),
                annotation=List[param.annotation] if is_list else param.annotation,
                kind=param.kind,
            )
            for param in sig.parameters.values()
        ],
        return_annotation=Optional[sig.return_annotation] if is_optional else sig.return_annotation,
    )
    parse.__signature__ = newsig

    return Depends(parse)

