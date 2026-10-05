# AWS KMS - Cifrado de Sobre con Python

## Código utilizado

```python
import boto3, base64, json
from cryptography.fernet import Fernet

kms = boto3.client("kms")

key = kms.create_key()["KeyMetadata"]["KeyId"]

d = kms.generate_data_key(
    KeyId=key,
    KeySpec="AES_256"
)

f = Fernet(base64.urlsafe_b64encode(d["Plaintext"]))

sobre = {
    "mensaje": f.encrypt(b"Hola AWS KMS").decode(),
    "key": base64.b64encode(d["CiphertextBlob"]).decode()
}

json.dump(sobre, open("sobre.json", "w"))

def descifrar(s):
    d = kms.decrypt(
        CiphertextBlob=base64.b64decode(s["key"])
    )["Plaintext"]

    print(
        "Mensaje:",
        Fernet(base64.urlsafe_b64encode(d))
        .decrypt(s["mensaje"].encode())
        .decode()
    )

    print("Key:", d.hex())

descifrar(sobre)

kms.schedule_key_deletion(
    KeyId=key,
    PendingWindowInDays=7
)
```

# Explicación detallada del código

## 1. Importaciones

```python
import boto3, base64, json
```

Se importan tres módulos:

- `boto3`: permite que Python se comunique con los servicios de AWS. En este caso se utiliza para trabajar con AWS KMS.
- `base64`: permite convertir datos binarios a una representación de texto Base64. Esto es necesario para poder guardar datos binarios dentro de un archivo JSON.
- `json`: permite crear y guardar información en formato JSON.

El programa utiliza estos módulos para comunicarse con KMS, convertir las claves a un formato que pueda guardarse y crear el archivo `sobre.json`.

## 2. Importación de Fernet

```python
from cryptography.fernet import Fernet
```

Se importa `Fernet` desde la biblioteca `cryptography`.

Fernet proporciona cifrado simétrico autenticado. Esto significa que la misma clave utilizada para cifrar un mensaje se utiliza posteriormente para descifrarlo.

En este proyecto, Fernet se utiliza para cifrar el mensaje:

```text
Hola AWS KMS
```

La clave que utiliza Fernet no se genera directamente por Fernet, sino que se obtiene mediante AWS KMS utilizando una Data Key.

## 3. Crear el cliente de AWS KMS

```python
kms = boto3.client("kms")
```

Aquí se crea un cliente para comunicarse con AWS Key Management Service (KMS).

Boto3 utiliza las credenciales configuradas en el entorno de AWS para realizar las operaciones.

A partir de este momento, la variable `kms` permite ejecutar operaciones como:

- Crear una KMS Key.
- Generar una Data Key.
- Descifrar una Data Key.
- Programar la eliminación de una KMS Key.

## 4. Crear la KMS Key

```python
key = kms.create_key()["KeyMetadata"]["KeyId"]
```

Esta instrucción solicita a AWS KMS que cree una nueva clave administrada por KMS.

`create_key()` devuelve información sobre la clave creada.

Dentro de esa información se encuentra:

```text
KeyMetadata
```

Y dentro de `KeyMetadata` se encuentra:

```text
KeyId
```

Por eso se utiliza:

```python
["KeyMetadata"]["KeyId"]
```

El resultado se guarda en:

```python
key
```

La variable `key` contiene el identificador de la KMS Key.

La KMS Key no se utiliza directamente para cifrar el mensaje. Su función principal en este ejemplo es proteger la Data Key.

## 5. Generar una Data Key

```python
d = kms.generate_data_key(
    KeyId=key,
    KeySpec="AES_256"
)
```

Aquí AWS KMS genera una Data Key.

Se especifica:

```python
KeyId=key
```

para indicar qué KMS Key se utilizará para proteger la Data Key.

También se especifica:

```python
KeySpec="AES_256"
```

Esto indica que la Data Key tendrá un tamaño de 256 bits.

AWS KMS devuelve dos versiones importantes de la Data Key:

```text
Plaintext
CiphertextBlob
```

`Plaintext` es la Data Key sin cifrar.

`CiphertextBlob` es la misma Data Key protegida mediante la KMS Key.

La respuesta se guarda en:

```python
d
```

## 6. ¿Por qué existen dos versiones de la Data Key?

Este comportamiento es fundamental para entender el concepto de Envelope Encryption.

La Data Key tiene dos representaciones:

```text
Data Key en texto plano
Data Key cifrada
```

La versión en texto plano se utiliza temporalmente para cifrar el mensaje.

La versión cifrada se almacena para poder recuperar posteriormente la Data Key utilizando AWS KMS.

El objetivo es no almacenar permanentemente la Data Key en texto plano.

El proceso es:

```text
KMS Key
   |
   v
Data Key
   |
   +---- Plaintext -> cifrar el mensaje
   |
   +---- CiphertextBlob -> guardar protegida
```

Esto corresponde al concepto de:

```text
Envelope Encryption
```

## 7. Crear el objeto Fernet

```python
f = Fernet(base64.urlsafe_b64encode(d["Plaintext"]))
```

Fernet necesita recibir una clave compatible con su formato.

La Data Key generada por KMS se encuentra en:

```python
d["Plaintext"]
```

Este valor es binario.

Por eso se transforma mediante:

```python
base64.urlsafe_b64encode(...)
```

Después de la conversión se utiliza como clave de Fernet.

Finalmente se crea:

```python
f
```

que representa el objeto utilizado para cifrar el mensaje.

## 8. Crear el sobre digital

```python
sobre = {
    "mensaje": f.encrypt(b"Hola AWS KMS").decode(),
    "key": base64.b64encode(d["CiphertextBlob"]).decode()
}
```

Aquí se crea un diccionario llamado:

```python
sobre
```

Este diccionario representa el sobre digital que posteriormente será guardado en un archivo JSON.

Contiene dos elementos:

```text
mensaje
key
```

### 8.1. Cifrar el mensaje

```python
f.encrypt(b"Hola AWS KMS").decode()
```

Primero se convierte el texto:

```text
Hola AWS KMS
```

a bytes utilizando:

```python
b"Hola AWS KMS"
```

Después se cifra mediante:

```python
f.encrypt(...)
```

Fernet genera el texto cifrado.

Finalmente:

```python
.decode()
```

convierte el resultado a texto para poder guardarlo dentro del JSON.

Por lo tanto:

```text
Hola AWS KMS
```

se transforma en un mensaje cifrado.

### 8.2. Guardar la Data Key cifrada

```python
base64.b64encode(d["CiphertextBlob"]).decode()
```

`CiphertextBlob` es binario.

Como JSON trabaja principalmente con texto, primero se convierte a Base64:

```python
base64.b64encode(...)
```

Después se convierte a texto:

```python
.decode()
```

El resultado se guarda dentro del campo:

```python
"key"
```

Es importante entender que esta no es la Data Key en texto plano.

Es la Data Key protegida por AWS KMS.

## 9. Guardar la Data Key cifrada

El resultado final de `sobre` tiene conceptualmente esta estructura:

```json
{
    "mensaje": "MENSAJE_CIFRADO",
    "key": "DATA_KEY_CIFRADA"
}
```

El mensaje está cifrado con la Data Key.

La Data Key está protegida mediante la KMS Key.

Por eso se forma una estructura de protección por capas.

## 10. Guardar `sobre.json`

```python
json.dump(sobre, open("sobre.json", "w"))
```

Esta instrucción crea el archivo:

```text
sobre.json
```

El modo:

```python
"w"
```

significa escritura.

El archivo contiene el mensaje cifrado y la Data Key cifrada.

El archivo representa el sobre digital que posteriormente será utilizado para realizar el proceso de descifrado.

## 11. Crear la función `descifrar`

```python
def descifrar(s):
```

Se crea una función llamada:

```text
descifrar
```

La función recibe un parámetro:

```python
s
```

En este caso `s` representa el contenido del sobre digital.

La función tiene como objetivo realizar el proceso inverso:

```text
Data Key cifrada
       |
       v
AWS KMS
       |
       v
Data Key original
       |
       v
Fernet
       |
       v
Mensaje original
```

## 12. Recuperar y descifrar la Data Key

```python
d = kms.decrypt(
    CiphertextBlob=base64.b64decode(s["key"])
)["Plaintext"]
```

Primero se recupera:

```python
s["key"]
```

que contiene la Data Key cifrada en Base64.

Como KMS necesita recibir los datos binarios originales, se utiliza:

```python
base64.b64decode(...)
```

Esto convierte nuevamente el texto Base64 en bytes.

Después se ejecuta:

```python
kms.decrypt(...)
```

AWS KMS utiliza la KMS Key correspondiente para descifrar la Data Key.

El resultado se obtiene mediante:

```python
["Plaintext"]
```

Ahora:

```python
d
```

contiene nuevamente la Data Key original.

## 13. Descifrar el mensaje

```python
Fernet(base64.urlsafe_b64encode(d))
.decrypt(s["mensaje"].encode())
.decode()
```

Primero se vuelve a preparar la Data Key para utilizarla con Fernet:

```python
base64.urlsafe_b64encode(d)
```

Después se crea nuevamente el objeto Fernet:

```python
Fernet(...)
```

El mensaje cifrado está almacenado en:

```python
s["mensaje"]
```

Se convierte a bytes mediante:

```python
.encode()
```

Después se descifra:

```python
.decrypt(...)
```

Finalmente:

```python
.decode()
```

convierte los bytes descifrados nuevamente en texto.

El resultado vuelve a ser:

```text
Hola AWS KMS
```

## 14. Mostrar el mensaje

```python
print(
    "Mensaje:",
    Fernet(base64.urlsafe_b64encode(d))
    .decrypt(s["mensaje"].encode())
    .decode()
)
```

Esta instrucción muestra en la terminal el mensaje después de haber sido descifrado.

El resultado esperado es:

```text
Mensaje: Hola AWS KMS
```

Esto demuestra que el proceso de cifrado y descifrado funcionó correctamente.

## 15. Mostrar la Data Key en hexadecimal

```python
print("Key:", d.hex())
```

La Data Key recuperada se encuentra en formato binario.

La función:

```python
.hex()
```

convierte esos bytes a una representación hexadecimal.

Esto permite visualizar la clave de una manera más fácil de leer en la terminal.

El objetivo principal de esta línea es mostrar la Data Key recuperada durante la demostración.

## 16. Ejecutar la función

```python
descifrar(sobre)
```

Aquí se llama a la función `descifrar`.

Se le entrega:

```python
sobre
```

que contiene:

```text
mensaje cifrado
Data Key cifrada
```

La función recupera la Data Key utilizando KMS y después utiliza esa Data Key para descifrar el mensaje.

## 17. Programar la eliminación de la KMS Key

```python
kms.schedule_key_deletion(
    KeyId=key,
    PendingWindowInDays=7
)
```

Finalmente se programa la eliminación de la KMS Key.

Se utiliza:

```python
KeyId=key
```

para identificar la clave creada anteriormente.

También:

```python
PendingWindowInDays=7
```

indica que la eliminación queda programada después de un periodo de espera de 7 días.

AWS KMS utiliza un periodo de espera para evitar eliminaciones accidentales inmediatas de claves.

La eliminación programada es una operación importante porque las claves KMS deben administrarse cuidadosamente.

## 18. Flujo completo

El funcionamiento completo del programa puede entenderse de la siguiente manera:

```text
1. Crear KMS Key
        |
        v
2. Generar Data Key
        |
        +----------------------+
        |                      |
        v                      v
 Plaintext              CiphertextBlob
        |                      |
        v                      v
   Fernet                Guardar protegida
        |
        v
 Cifrar mensaje
        |
        v
 Guardar sobre.json
        |
        v
 Recuperar CiphertextBlob
        |
        v
 AWS KMS decrypt
        |
        v
 Recuperar Data Key
        |
        v
 Fernet decrypt
        |
        v
 Mensaje original
```

## 19. Envelope Encryption

El concepto principal utilizado en este ejercicio es:

```text
Envelope Encryption
```

Envelope Encryption consiste en utilizar una clave para proteger otra clave.

En este caso:

```text
KMS Key
    |
    v
protege
    |
    v
Data Key
    |
    v
protege
    |
    v
Mensaje
```

La KMS Key no se utiliza directamente para cifrar el mensaje.

En lugar de eso, KMS genera una Data Key.

La Data Key se utiliza para cifrar el contenido.

Después, la KMS Key protege la Data Key.

Esto permite trabajar de forma eficiente con datos y mantener la clave principal administrada por AWS KMS.

## 20. Tabla de elementos

| Elemento | Función |
|---|---|
| `boto3` | Permite comunicarse con AWS |
| AWS KMS | Administra y protege las claves |
| KMS Key | Protege la Data Key |
| Data Key | Se utiliza para cifrar el mensaje |
| Fernet | Realiza el cifrado y descifrado simétrico |
| Base64 | Permite representar datos binarios como texto |
| JSON | Permite almacenar el sobre |
| `sobre.json` | Contiene el mensaje cifrado y la Data Key cifrada |
| `descifrar()` | Recupera la clave y descifra el mensaje |

## 21. Cinco ideas principales

### 1. AWS KMS administra la clave principal

La KMS Key es creada y administrada mediante AWS KMS.

### 2. La Data Key se utiliza para cifrar el mensaje

El mensaje se cifra utilizando Fernet y la Data Key generada por KMS.

### 3. La Data Key también se protege

La versión cifrada de la Data Key se guarda dentro del sobre digital.

### 4. El mensaje no se guarda en texto plano

En `sobre.json` se almacena el mensaje cifrado.

### 5. Se utiliza Envelope Encryption

Una clave protege otra clave, y esa segunda clave protege los datos.

## 22. Respuesta para defensa oral

Si el profesor pregunta:

**¿Qué hace el programa?**

La respuesta puede ser:

> El programa utiliza AWS KMS para crear una KMS Key y generar una Data Key. La Data Key se utiliza con Fernet para cifrar el mensaje. Luego, la versión cifrada de la Data Key se guarda en un archivo JSON. Para descifrar, AWS KMS recupera la Data Key y posteriormente Fernet utiliza esa clave para recuperar el mensaje original.

Si pregunta:

**¿Qué es Envelope Encryption?**

Se puede responder:

> Es una técnica donde una clave se utiliza para proteger otra clave. En este caso, AWS KMS protege la Data Key y la Data Key se utiliza para cifrar el mensaje.

Si pregunta:

**¿Por qué se utiliza Base64?**

Se puede responder:

> Porque algunas respuestas de AWS KMS son datos binarios y JSON trabaja con valores de texto. Base64 permite representar esos datos binarios como texto para almacenarlos en el archivo JSON.

## 23. Archivos generados

El programa genera:

```text
sobre.json
```

Este archivo contiene conceptualmente:

```json
{
    "mensaje": "mensaje cifrado",
    "key": "Data Key cifrada"
}
```

El archivo no contiene directamente la Data Key en texto plano.

## 24. Resultado esperado

Al ejecutar el programa correctamente, la función `descifrar()` debe mostrar un resultado equivalente a:

```text
Mensaje: Hola AWS KMS
Key: [representación hexadecimal de la Data Key]
```

Esto demuestra que:

1. La KMS Key fue creada.
2. La Data Key fue generada.
3. El mensaje fue cifrado.
4. La Data Key cifrada fue almacenada.
5. AWS KMS pudo recuperar la Data Key.
6. Fernet pudo descifrar el mensaje.
7. El mensaje original fue recuperado.

## 25. Resumen final

El programa implementa un ejemplo de cifrado utilizando AWS KMS, Data Keys, Fernet y Envelope Encryption.

El proceso comienza creando una KMS Key.

Después AWS KMS genera una Data Key.

La versión en texto plano de la Data Key se utiliza temporalmente para cifrar el mensaje mediante Fernet.

La versión protegida de la Data Key se almacena en el archivo `sobre.json`.

Cuando se necesita descifrar el contenido, AWS KMS recupera la Data Key original utilizando la KMS Key.

Después Fernet utiliza nuevamente la Data Key para descifrar el mensaje.

Finalmente se obtiene:

```text
Hola AWS KMS
```

De esta manera se demuestra el funcionamiento de un esquema de cifrado por capas, donde AWS KMS protege la Data Key y la Data Key protege los datos.

El punto central del ejercicio es comprender que AWS KMS no tiene que cifrar directamente todo el contenido. Puede utilizarse para proteger las claves que posteriormente se utilizan para cifrar los datos. Este mecanismo es conocido como Envelope Encryption.
