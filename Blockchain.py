import hashlib
import json
from time import time

class Client:
    """
    Classe représentant un client dans la blockchain.

    Attributs:
        nom (str): Le nom du client.
        solde (float): Le solde du client.
    """
    
    def __init__(self, nom, solde_initial):
        self.nom = nom  # Nom du client
        self.solde = solde_initial  # Solde du client

    def debiter(self, montant):
        """
        Débite le solde du client.

        Variables:
            montant (float): Le montant à débiter.
        """
        self.solde -= montant

    def crediter(self, montant):
        """
        Crédite le solde du client.

        Variables:
            montant (float): Le montant à créditer.
        """
        self.solde += montant

class Noeud:
    """
    Classe représentant un nœud dans l'arbre Merkle.

    Attributs:
        data (str): Les données du nœud (hachage).
        left (Noeud): Le nœud fils gauche.
        right (Noeud): Le nœud fils droit.
    """
    
    def __init__(self, data):
        self.data = data  # Données du nœud
        self.left = None  # Référence vers le nœud gauche
        self.right = None  # Référence vers le nœud droit

    def est_feuille(self):
        """
        Vérifie si le nœud est une feuille (n'a pas d'enfants).

        Retour:
            bool: True si le nœud est une feuille, sinon False.
        """
        return self.left is None and self.right is None

class ArbreMerkle:
    """
    Classe représentant un arbre Merkle.

    Attributs:
        racine (Noeud): Le nœud racine de l'arbre.
        racine_merkle (str): Le hachage de la racine Merkle.
    """
    def __init__(self):
        self.racine = None  # Racine de l'arbre
        self.racine_merkle = None  # Racine de Merkle de l'arbre

    def fonction_hachage(self, data):
        """
        Calcule le hachage SHA-256 d'une chaîne de caractères.

        Variables:
            data (str): La chaîne de caractères à hacher.

        Retour:
            str: Le hachage résultant.
        """
        return hashlib.sha256(data.encode()).hexdigest()

    def build_arbre(self, transactions):
        """
        Construit l'arbre Merkle à partir d'une liste de transactions.

        Variables:
            transactions (list): Liste des transactions (chaînes de caractères).
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
                parent.left = noeud1  # type: ignore
                parent.right = noeud2 # type: ignore
                new_level_tree.append(parent)
            noeuds = new_level_tree
        self.racine = noeuds[0]
        self.racine_merkle = self.racine.data

    def obtenir_racine_merkle(self):
        """
        Renvoie le hachage de la racine Merkle.

        Retour:
            str: Le hachage de la racine Merkle.
        """
        return self.racine_merkle

    def verifier_transaction(self, transaction):
        """
        Vérifie si une transaction est valide dans l'arbre Merkle.

        Variables:
            transaction (str): La transaction à vérifier (chaîne de caractères).

        Retour:
            bool: True si la transaction est valide, sinon False.
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
    Classe représentant une blockchain.

    Attributs:
        chaine (list): La chaîne de blocs.
        transactions_courantes (list): Liste des transactions en attente.
        arbre_merkle (ArbreMerkle): L'arbre Merkle pour les transactions.
        clients (dict): Dictionnaire des clients (identifiant -> Client).
    """
    def __init__(self):
        self.chaine = []  # Chaîne de blocs
        self.transactions_courantes = []  # Liste des transactions en attente
        self.arbre_merkle = ArbreMerkle()  # Arbre de Merkle pour les transactions
        self.clients = {}  # Clients de la blockchain
        self.charger_clients()  # Charge les clients à partir d'un fichier JSON
        self.nouveau_bloc(proof=1000, hash_precedent=1)  # Crée le premier bloc initial


    def ajouter_client(self, identifiant, nom, solde_initial):
        """
        Ajoute un nouveau client à la blockchain.

        Variables:
            identifiant (str): L'identifiant unique du client.
            nom (str): Le nom du client.
            solde_initial (float): Le solde initial du client.
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
        Traite les transactions en mettant à jour les soldes des clients.

        Retour:
            bool: True si toutes les transactions sont valides, sinon False.
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
        Crée un nouveau bloc dans la chaîne.

        Variables:
            proof (int): La preuve de travail (Proof of Work) du bloc.
            hash_precedent (str): Le hachage du bloc précédent (facultatif).

        Retour:
            dict: Le nouveau bloc créé.
        """
        self.build_arbre_merkle()
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
        Renvoie le dernier bloc de la chaîne.

        Retour:
            dict: Le dernier bloc.
        """
        return self.chaine[-1]

    def nouvelle_transaction(self, envoyeur, destinataire, montant):
        """
        Ajoute une nouvelle transaction à la liste des transactions en attente.

        Variables:
            envoyeur (str): L'identifiant de l'expéditeur.
            destinataire (str): L'identifiant du destinataire.
            montant (float): Le montant de la transaction.

        Retour:
            int: L'index du prochain bloc (ou None si la transaction a échoué).
        """
        if envoyeur not in self.clients or destinataire not in self.clients:
            print("Transaction echouee: Client non trouve.")
            return None
        transaction = {'envoyeur': envoyeur, 'destinataire': destinataire, 'montant': montant}
        self.transactions_courantes.append(transaction)
        self.sauvegarder_transac_history()  # Sauvegarde des transactions courantes
        if self.process_transactions():
            self.build_arbre_merkle()
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
        Calcule le hachage SHA-256 d'un bloc.

        Variables:
            bloc (dict): Le bloc à hacher.

        Retour:
            str: Le hachage résultant.
        """
        bloc_string = json.dumps(bloc, sort_keys=True).encode()
        return hashlib.sha256(bloc_string).hexdigest()

    def proof_of_work(self, last_proof):
        """
        Effectue la preuve de travail (Proof of Work) pour trouver un nouveau proof.

        Variables:
            last_proof (int): La preuve de travail du dernier bloc.

        Retour:
            int: Le nouveau proof.
        """
        proof = 0
        while not self.valider_proof(last_proof, proof):
            proof += 1
#           print(proof)  # Incrementation du compteur a chaque essai
        return proof

    @staticmethod

    def valider_proof(last_proof, proof):
        """
        Valide la preuve de travail en vérifiant que la combinaison de la dernière preuve et de la nouvelle preuve
        génère un hash commençant par quatre zéros.

        Args:
            last_proof (int): La preuve précédente.
            proof (int): La nouvelle preuve.

        Returns:
            bool: True si la nouvelle preuve est valide, False sinon.
        """
        essai = f'{last_proof}{proof}'.encode()
        essai_hash = hashlib.sha256(essai).hexdigest()
        return essai_hash[:4] == "0000"

    def build_arbre_merkle(self):
        """
        Construit un arbre de Merkle à partir des transactions courantes.
        Cette méthode convertit chaque transaction courante en une chaîne JSON triée par clés,
        puis utilise cette liste de transactions pour construire l'arbre de Merkle.
        """
        transactions = [json.dumps(transac, sort_keys=True) for transac in self.transactions_courantes]
        self.arbre_merkle.build_arbre(transactions)

    def verifier_transaction_dans_arbre_merkle(self, transaction):
        """
        Vérifie si une transaction donnée se trouve dans l'arbre de Merkle.
        Args:
            transaction (dict): La transaction à vérifier.
        Returns:
            bool: True si la transaction est présente dans l'arbre de Merkle, False sinon.
        """
        transaction_str = json.dumps(transaction, sort_keys=True)
        return self.arbre_merkle.verifier_transaction(transaction_str)


# MAIN
blockchain = Blockchain()

# Ajouter une nouvelle transaction et verifier automatiquement
index = blockchain.nouvelle_transaction("charles123", "bob", 100)

# Proof of Work
dernier_bloc = blockchain.dernier_bloc
last_proof = dernier_bloc['proof']  # Récupère la preuve du dernier bloc
proof = blockchain.proof_of_work(last_proof) # Calcule une nouvelle preuve

# Creer un nouveau bloc
hash_precedent = blockchain.hash(dernier_bloc) # Calcule le hachage du bloc précédent
nouveau_bloc_mine = blockchain.nouveau_bloc(proof, hash_precedent) # Crée un nouveau bloc avec la preuve et le hachage précédent
