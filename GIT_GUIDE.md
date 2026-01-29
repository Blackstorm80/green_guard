# Guide de Contribution avec Git pour GreenGuard

Ce document est une mini-formation pour vous aider à utiliser Git correctement dans le cadre du projet GreenGuard. L'objectif est de maintenir une version saine et stable de notre code sur la branche principale (`main`).

## Règle d'Or : Ne Jamais Travailler sur `main`

La branche `main` (parfois appelée `master`) est considérée comme la source de vérité. Elle doit **toujours** contenir une version fonctionnelle et stable du projet. Personne ne doit jamais y apporter de modifications directement.

Tout le travail doit se faire dans des **branches séparées**.

---

## Workflow de Développement Étape par Étape

Voici le processus à suivre pour chaque nouvelle fonctionnalité, correction de bug, ou modification.

### 1. Se Synchroniser avec la Branche Principale

Avant de commencer quoi que ce soit, assurez-vous que votre version locale de `main` est à jour.

```bash
# 1. Allez sur la branche main
git checkout main

# 2. Récupérez les dernières modifications depuis le serveur distant (origin)
git pull origin main
```

### 2. Créer une Nouvelle Branche

Créez une branche dédiée à votre tâche. Le nom de la branche doit être descriptif et préfixé par son type.

```bash
# Syntaxe : git checkout -b <type>/<description-courte>

# Exemple pour une nouvelle fonctionnalité :
git checkout -b feature/authentification-utilisateur

# Exemple pour une correction de bug :
git checkout -b fix/erreur-calcul-stress-hydrique
```
*   **Types courants :** `feature` (nouvelle fonctionnalité), `fix` (correction de bug), `docs` (documentation), `style` (mise en forme), `refactor` (refonte de code).

### 3. Travailler et "Commiter"

Faites vos modifications dans le code. Une fois qu'une étape logique est terminée, faites un "commit". Essayez de faire des commits petits et ciblés.

```bash
# 1. Ajoutez les fichiers que vous avez modifiés
git add . # Ajoute tous les fichiers modifiés

# 2. Créez le commit avec un message clair
git commit -m "feat: Ajoute le formulaire de connexion"
```

### 4. Pousser la Branche sur le Serveur

Lorsque vous êtes prêt à partager votre travail (même s'il n'est pas fini), poussez votre branche sur le serveur distant.

```bash
# La première fois, utilisez -u pour lier votre branche locale à la branche distante
git push -u origin feature/authentification-utilisateur
```

### 5. Créer une "Pull Request" (PR)

Une fois votre travail terminé et poussé, allez sur la plateforme (GitHub, GitLab, etc.) :
1.  Vous verrez une notification vous proposant de créer une **Pull Request** pour votre branche.
2.  Cliquez dessus, donnez un titre et une description clairs à votre PR.
3.  Assignez un ou plusieurs relecteurs (les autres membres de l'équipe).

La Pull Request est une demande pour fusionner votre travail dans `main`. Elle permet aux autres de relire votre code, de laisser des commentaires et de s'assurer que tout fonctionne avant la fusion.

### 6. Après la Fusion

Une fois votre PR validée et fusionnée dans `main` :
1.  Vous pouvez supprimer votre branche de travail.
2.  Retournez à l'étape 1 pour vous synchroniser avec `main` avant de commencer une nouvelle tâche.