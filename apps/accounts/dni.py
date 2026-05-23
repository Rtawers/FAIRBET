def calcular_digito_verificador(dni_str: str) -> str:
    pesos = [3, 2, 7, 6, 5, 4, 3, 2]
    suma = sum(int(dni_str[i]) * pesos[i] for i in range(8))
    residuo = suma % 11
    
    tabla_mapeo = {
        0: "K", 1: "0", 2: "1", 3: "2", 4: "3", 5: "4",
        6: "5", 7: "6", 8: "7", 9: "8", 10: "9"
    }
    return tabla_mapeo[residuo]