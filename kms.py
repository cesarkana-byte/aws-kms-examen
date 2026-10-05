import boto3,base64,json
from cryptography.fernet import Fernet

kms=boto3.client("kms")
key=kms.create_key()["KeyMetadata"]["KeyId"]
d=kms.generate_data_key(KeyId=key,KeySpec="AES_256")
f=Fernet(base64.urlsafe_b64encode(d["Plaintext"]))

sobre={"mensaje":f.encrypt(b"Hola AWS KMS").decode(),
       "key":base64.b64encode(d["CiphertextBlob"]).decode()}
json.dump(sobre,open("sobre.json","w"))

def descifrar(s):
    d=kms.decrypt(CiphertextBlob=base64.b64decode(s["key"]))["Plaintext"]
    print("Mensaje:",f.decrypt(s["mensaje"].encode()).decode())
    print("Key:",d.hex())

descifrar(sobre)
kms.schedule_key_deletion(KeyId=key,PendingWindowInDays=7)
