from pydantic import BaseModel, ConfigDict

from app.models.enums import ProductType


class SupplierBase(BaseModel):
    code: str
    name: str
    contact_email: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    erp_reference_no: str | None = None


class SupplierCreate(SupplierBase):
    pass


class SupplierOut(SupplierBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class CustomerBase(BaseModel):
    code: str
    name: str
    contact_email: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    erp_reference_no: str | None = None


class CustomerCreate(CustomerBase):
    pass


class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ProductBase(BaseModel):
    sku: str
    name: str
    category: str | None = None
    uom: str = "EA"
    product_type: ProductType = ProductType.RAW_MATERIAL
    description: str | None = None
    erp_reference_no: str | None = None


class ProductCreate(ProductBase):
    pass


class ProductOut(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
