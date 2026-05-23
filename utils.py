# Para los rnd
def format_rnd(value) -> str:
    # Ve si valor de tabla era vacio lo deja con -
    if value is None or value == "" or value == "-":
        return "-"
    # Si no lo transforma en valor decimal--> con 4 decim ales
    return f"{float(value):.4f}"

# Hace lo mismo pero para los valores de tiempo
def format_time(value) -> str:
    if value is None or value == "" or value == "-":
        return "-"
    return f"{float(value):.4f}"

