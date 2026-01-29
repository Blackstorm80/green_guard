Voici une section que tu peux ajouter à ton fichier de formation, spéciale pour la config Git + Git Bash pour pousser facilement (une fois, puis tranquille).

***

## 11. Configurer Git et Git Bash pour pousser facilement

Objectif : que chaque membre de l’équipe puisse faire `git push` sans galérer à chaque fois.

### 11.1. Configurer son identité Git (une fois)

Dans **Git Bash**, chaque membre doit configurer son nom et son email (les mêmes que sur GitHub de préférence) :

```bash
git config --global user.name "Prénom Nom"
git config --global user.email "email@example.com"
```

Pour vérifier :

```bash
git config --global --list
```

***

### 11.2. Générer une clé SSH pour GitHub (une fois par machine)

1. Ouvrir **Git Bash**.  
2. Générer une clé SSH :

```bash
ssh-keygen -t ed25519 -C "votre_email_github"
```

- Appuyer sur **Entrée** quand il demande le chemin.  
- Appuyer sur **Entrée** pour la passphrase (ou en mettre une si vous voulez).

3. Afficher la clé publique :

```bash
cat ~/.ssh/id_ed25519.pub
```

4. Copier TOUT le contenu affiché.

***

### 11.3. Ajouter la clé SSH sur GitHub

1. Aller sur GitHub → cliquer sur l’avatar en haut à droite → **Settings**.  
2. Menu à gauche → **SSH and GPG keys** → **New SSH key**.  
3. Donner un nom (ex. “PC perso Annael”) et coller la clé dans le champ “Key”.  
4. Enregistrer.

***

### 11.4. Configurer le dépôt pour utiliser SSH

Dans Git Bash, à la racine du projet `green_guard` :

```bash
git remote -v
```

Si vous voyez une URL en `https://github.com/...`, changez-la pour SSH :

```bash
git remote set-url origin git@github.com:Blackstorm80/green_guard.git
```

(ou adapter avec le bon nom d’utilisateur / repo)

Tester la connexion :

```bash
ssh -T git@github.com
```

- Si tout va bien, GitHub répondra par un message du style :  
  `Hi VOTRE_USER! You've successfully authenticated, but GitHub does not provide shell access.`  
  → C’est normal et c’est bon signe.

***

### 11.5. Pousser ensuite devient simple

Une fois tout ça fait, pour ce projet :

1. Coder + commit :

```bash
git add .
git commit -m "feat: message clair"
```

2. Pousser :

```bash
git push
```

- Si une passphrase a été mise sur la clé SSH, Git la demandera de temps en temps.  
- Sinon, ça part direct sans retaper mot de passe GitHub ou token.

***

### 11.6. Résumé pour l’équipe

Chaque membre doit :

1. Configurer `user.name` et `user.email`.  
2. Créer UNE clé SSH sur sa machine.  
3. Ajouter cette clé dans son compte GitHub.  
4. Mettre l’URL du remote du projet en `git@github.com:...`.  

Ensuite, le cycle devient :  

```bash
git pull
git add .
git commit -m "..."
git push
```
, ceci est a faire une seule fois ...