#[derive(Debug, PartialEq, Clone)]
pub enum Type {
    Int, String, Class(Box<Type>),
    Generic(String),
}
impl Type {
    pub fn from_str(type_str: &str) -> Result<Type, String> {
        match type_str {
            "int" => Ok(Type::Int),
            "string" => Ok(Type::String),
            _ => Ok(Type::Generic(type_str.to_string())),
        }
    }
}