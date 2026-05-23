def calcular_digito_verificador(dni_str: str) -> str:
    if len(dni_str) < 8:
        raise ValueError("El DNI debe tener al menos 8 dígitos")
        
    if not dni_str.isdigit():
        raise ValueError("El DNI solo debe contener caracteres numericos")
        
    pesos = [3, 2, 7, 6, 5, 4, 3, 2]
    suma = sum(int(dni_str[i]) * pesos[i] for i in range(8))
    residuo = suma % 11
    
    tabla_mapeo = {
        0: "K", 1: "0", 2: "1", 3: "2", 4: "3", 5: "4",
        6: "5", 7: "6", 8: "7", 9: "8", 10: "9"
    }
    
    return tabla_mapeo[residuo]

def validar_dni(dni_completo: str) -> bool:
    if len(dni_completo) != 9:
        raise ValueError("El DNI completo debe tener 9 caracteres")
        
    numeros = dni_completo[:8]
    digito_recibido = dni_completo[8].upper() 
    
    digito_correcto = calcular_digito_verificador(numeros)
    
    if digito_recibido != digito_correcto:
        raise ValueError("El dígito verificador es incorrecto")
        
    return True