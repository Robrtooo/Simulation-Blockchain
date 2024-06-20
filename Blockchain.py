import hashlib
import json
from time import time

class Client:
    """
    Représente un client dans le système de la blockchain.
    """
    
    def __init__(self, nom, solde_initial):
        """
        Initialise un nouveau client avec un nom et un solde initial.
        """
        self.nom = nom  # Nom du client
        self.solde = solde_initial  # Solde du client

    def debiter(self, montant):
        """
        Débite le solde du client.
        """
        self.solde -= montant

    def crediter(self, montant):
        """
        Crédite le solde du client.
        """
        self.solde += montant

class Noeud:
    """
    Représente un nœud dans la construction d'un arbre.
    """
    
    def __init__(self, data):
        """
        Initialise un nœud avec des données.
        """
        self.data = data  # Données du nœud
        self.left = None  # Référence vers le nœud gauche
        self.right = None  # Référence vers le nœud droit

    def est_feuille(self):
        """
        Vérifie si le nœud est une feuille (sans nœuds enfants).
        """
        return self.left is None and self.right is None

class ArbreMerkle:
    """
    Représente un arbre de Merkle utilisé pour la vérification des transactions.
    """
    
    def __init__(self):
        """
        Initialise un arbre de Merkle avec une racine et une racine de Merkle.
        """
        self.racine = None  # Racine de l'arbre
        self.racine_merkle = None  # Racine de Merkle de l'arbre

    def fonction_hachage(self, data):
        """
        Effectue une fonction de hachage SHA-256 sur les données.
        """
        return hashlib.sha256(data.encode()).hexdigest()

    def build_arbre_merkle(self, transactions):
        """
        Construit l'arbre de Merkle à partir d'une liste de transactions.
        """
        noeuds = [Noeud(self.fonction_hachage(t)) for t in transactions]
        if len(noeuds) == 0:
            return None
        while len(noeuds) > 1:
            new_level_tree = []
            for i in range(0, len(noeuds), 2):
                noeud1 = noeuds[i]
                noeud2 = noeuds[i + 1] if i + 1 < len(noeuds) else Noeud(noeuds[i].data)
                hash_data = noeud1.data + noeud2.data
                parent = Noeud(self.fonction_hachage(hash_data))
                parent.left = noeud1
                parent.right = noeud2
                new_level_tree.append(parent)
            noeuds = new_level_tree
        self.racine = noeuds[0]
        self.racine_merkle = self.racine.data

    def obtenir_racine_merkle(self):
        """
        Obtient la racine de Merkle de l'arbre.
        """
        return self.racine_merkle

    def verifier_transaction(self, transaction):
        """
        Vérifie si une transaction donnée existe dans l'arbre de Merkle.
        """
        hash_transaction = self.fonction_hachage(transaction)
        noeud_courant = self.racine

        def parcours(noeud):
            """
            Fonction récursive pour parcourir l'arbre.
            """
            if noeud.est_feuille():
                return noeud.data == hash_transaction
            if noeud.left and parcours(noeud.left):
                return True
            if noeud.right and parcours(noeud.right):
                return True
            return False
        return parcours(noeud_courant)

class Blockchain:
    """
    Représente une blockchain pour gérer les transactions et les blocs.
    """

    def __init__(self):
        """
        Initialise une nouvelle blockchain avec une chaîne vide et d'autres éléments nécessaires.
        """
        self.chaine = []  # Chaîne de blocs
        self.transactions_courantes = []  # Liste des transactions actuelles
        self.arbre_merkle = ArbreMerkle()  # Arbre de Merkle 
        self.clients = {}  # Clients de la blockchain
        self.charger_clients()  # Charge les clients à partir d'un fichier JSON
        self.nouveau_bloc(proof=1000, hash_precedent=1)  # Crée le premier bloc initial

    def ajouter_client(self, identifiant, nom, solde_initial):
        """
        Ajoute un nouveau client à la blockchain.
        """
        if identifiant not in self.clients:
            self.clients[identifiant] = Client(nom, solde_initial)
            self.sauvegarder_clients()

    def sauvegarder_clients(self):
        """
        Sauvegarde les données des clients dans un fichier JSON.
        """
        with open('clients.json', 'w') as file:
            clients_data = {identifiant: {'nom': client.nom, 'solde': client.solde} for identifiant, client in self.clients.items()}
            json.dump(clients_data, file, indent=4)

    def charger_clients(self):
        """
        Charge les données des clients à partir d'un fichier JSON.
        """
        try:
            with open('clients.json', 'r') as file:
                clients_data = json.load(file)
                for identifiant, data in clients_data.items():
                    self.clients[identifiant] = Client(data['nom'], data['solde'])
        except FileNotFoundError:
            pass

    def obtenir_solde_client(self, identifiant):
        """
        Obtient le solde d'un client donné.
        """
        if identifiant in self.clients:
            return self.clients[identifiant].solde
        return None

    def process_transactions(self):
        """
        Traite les transactions courantes en débitant et créditant les comptes des clients.
        """
        for transac in self.transactions_courantes:
            envoyeur = transac['envoyeur']
            destinataire = transac['destinataire']
            montant = transac['montant']
            if self.clients[envoyeur].solde < montant:
                return False
            self.clients[envoyeur].debiter(montant)
            self.clients[destinataire].crediter(montant)
        self.sauvegarder_clients()
        return True

    def nouveau_bloc(self, proof, hash_precedent=None):
        """
        Crée un nouveau bloc dans la chaîne de blocs.
        """
        self.sauvegarder_transac_json()
        bloc = {
            'index': len(self.chaine) + 1,
            'timestamp': time(),
            'transactions': self.transactions_courantes,
            'proof': proof,
            'hash_precedent': hash_precedent or self.hash(self.chaine[-1]),
            'racine_merkle': self.arbre_merkle.obtenir_racine_merkle()
        }
        self.transactions_courantes = []
        self.chaine.append(bloc)
        return bloc

    @property
    def dernier_bloc(self):
        """
        Obtient le dernier bloc ajouté à la chaîne de blocs.
        """
        return self.chaine[-1]

    def nouvelle_transaction(self, envoyeur, destinataire, montant):
        """
        Ajoute une nouvelle transaction à la liste des transactions courantes.
        """
        if envoyeur not in self.clients or destinataire not in self.clients:
            print("Transaction echouee: Client non trouve.")
            return None
        transaction = {'envoyeur': envoyeur, 'destinataire': destinataire, 'montant': montant}
        self.transactions_courantes.append(transaction)
        self.sauvegarder_transac_history()  # Sauvegarde des transactions 
        if self.process_transactions():
            self.sauvegarder_transac_json()
            transaction_verifiee = self.verifier_transaction_dans_arbre_merkle(transaction)
            if transaction_verifiee:
                print("La transaction a ete verifiee avec succes")
            else:
                print("La transaction n'a pas pu etre verifiee")
            return self.dernier_bloc['index'] + 1
        else:
            self.transactions_courantes.pop()
            print("Transaction echouee: Solde insuffisant.")
            return None

    def sauvegarder_transac_history(self):
        """
        Sauvegarde l'historique des transactions dans un fichier JSON.
        """
        try:
            with open('TransacHistory.json', 'r') as file:
                transac_history = json.load(file)
        except FileNotFoundError:
            transac_history = []
            print("Impossible de trouver le fichier TransacHistory.json")

        transac_history.extend(self.transactions_courantes)

        with open('TransacHistory.json', 'w') as file:
            json.dump(transac_history, file, indent=4)

    def hash(self, bloc):
        """
        Effectue une fonction de hachage SHA-256 sur un bloc donné
        """
        bloc_string = json.dumps(bloc, sort_keys=True).encode()
        return hashlib.sha256(bloc_string).hexdigest()

    def verifier_nonce(self, last_proof):
        """
        Effectue le Proof of Work en trouvant un nombre 'proof' tel que le hash commence par '0000'.
        """
        proof = 0
        while not self.proof_of_work(last_proof, proof):
            proof += 1
        return proof

    def proof_of_work(self, last_proof, proof):
        """
        Valide le Proof of Work : est-ce que le hash(last_proof, proof) commence par '0000' ?
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        #print('essai numero', guess)
        return guess_hash[:4] == "0000"

    def sauvegarder_transac_json(self):
        """
        Permet de sauvegarder les transactions courantes dans un fichier JSON.
        """
        self.arbre_merkle.build_arbre_merkle([json.dumps(tx) for tx in self.transactions_courantes]) #tx = transaction

    def verifier_transaction_dans_arbre_merkle(self, transaction):
        """
        Vérifie si une transaction existe déjà dans l'arbre de Merkle.
        Renvoie un booléen indiquant si la transaction est valide.
        """
        #hashed_transac = transaction + ['transaction' = ] faire en sorte de concatener à la liste les différents hashage des blocs ) l'intérieur de la blockchain
        transaction_str = json.dumps(transaction)
        return self.arbre_merkle.verifier_transaction(transaction_str)

# MAIN

blockchain = Blockchain()

add_client1 = blockchain.ajouter_client("charles123", "Charles", 10000)
add_client2 = blockchain.ajouter_client("bob", "Bob", 20000)

# Ajouter une nouvelle transaction et verifier automatiquement
index = blockchain.nouvelle_transaction("charles123", "bob", 1000)
#blockchain.nouvelle_transaction("bob", "charles123", 1000)

# Parcourir tous les blocs dans la blockchain
for bloc in blockchain.chaine:
    # Obtenir le hachage du bloc
    bloc_hash = blockchain.hash(bloc)
    # Imprimer le hachage du bloc
    print("Hash du bloc: ", bloc_hash)

print("Transaction ajoutee au bloc: ", index)
# Proof of Work
dernier_bloc = blockchain.dernier_bloc

last_proof = dernier_bloc['proof']
proof = blockchain.verifier_nonce(last_proof)

print("Proof of Work trouve: ", proof)


# Creer un nouveau bloc
hash_precedent = blockchain.hash(dernier_bloc)
nouveau_bloc_mine = blockchain.nouveau_bloc(proof, hash_precedent)
print("Nouveau bloc mine !", nouveau_bloc_mine)
