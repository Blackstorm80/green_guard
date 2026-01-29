# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

---

## 🤝 Workflow de Contribution avec Git

Pour garantir la stabilité du projet, il est **impératif** de suivre ces règles :

1.  **Ne jamais travailler directement sur la branche `main` (ou `master`).**
2.  Pour chaque nouvelle fonctionnalité ou correction, **créez toujours une nouvelle branche** à partir de `main`.
3.  Nommez votre branche de manière descriptive (ex: `feature/login-page` ou `fix/display-bug`).
4.  Une fois votre travail terminé, ouvrez une **Pull Request (PR)** pour demander la fusion de votre branche dans `main`.

Pour un guide détaillé sur les commandes Git et notre workflow, veuillez consulter le fichier `GIT_GUIDE.md` à la racine du projet.
