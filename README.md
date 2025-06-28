# AgentForge 🚀

<p align="center">
  <strong>The IDE for building AI-powered applications.</strong>
  <br />
  Describe your agent in a form, and AgentForge generates the complete source code, ready to run and refine.
</p>

<p align="center">
  <!-- Badges: Replace YOUR_USERNAME with your GitHub username -->
  <a href="https://github.com/MuhammadMaazA/AgentForge/blob/main/LICENSE"><img src="https://img.shields.io/github/license/MuhammadMaazA/AgentForge?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/MuhammadMaazA/AgentForge/graphs/contributors"><img src="https://img.shields.io/github/contributors/MuhammadMaazA/AgentForge?style=for-the-badge" alt="Contributors"></a>
  <img src="https://img.shields.io/github/repo-size/MuhammadMaazA/AgentForge?style=for-the-badge" alt="Repo Size">
  <img src="https://img.shields.io/github/last-commit/MuhammadMaazA/AgentForge?style=for-the-badge" alt="Last Commit">
</p>

<hr />

## ✨ Demo

<p align="center">
  <!-- IMPORTANT: Replace this with a real GIF of your application in action! -->
  <img src="https://raw.githubusercontent.com/MuhammadMaazA/AgentForge/main/assets/demo.gif" alt="AgentForge Demo GIF">
</p>

## 🎯 The Problem We Solve

Building AI applications involves repetitive boilerplate: setting up API clients, structuring frontend-backend communication, and writing basic UI code. This slows down innovation and makes it hard to quickly prototype new ideas.

**AgentForge changes that.** We abstract the tedious setup into a simple, declarative form. You focus on *what* your AI agent should do, and we handle the *how*, generating a ready-to-use Streamlit application in seconds.

## 🛠️ Tech Stack

AgentForge is a full-stack monorepo built with modern, scalable technologies.

| Area      | Technology                                                                                                  |
| :-------- | :---------------------------------------------------------------------------------------------------------- |
| **Frontend**  | [**Next.js**](https://nextjs.org/), [**React**](https://react.dev/), [**TypeScript**](https://www.typescriptlang.org/) |
| **Backend**   | [**Python**](https://www.python.org/), [**FastAPI**](https://fastapi.tiangolo.com/)                         |
| **Styling**   | [**Tailwind CSS**](https://tailwindcss.com/)                                                                 |
| **AI Core**   | [**OpenAI API**](https://platform.openai.com/) (GPT-4o)                                                    |

This repository currently provides a minimal FastAPI backend and a basic Next.js
frontend to kickstart development.

## 🚀 Getting Started

Ready to run AgentForge locally? Follow these steps.

### Prerequisites

- [Node.js](https://nodejs.org/en/) (v18 or later)
- [Python](https://www.python.org/downloads/) (v3.9 or later)
- An [OpenAI API Key](https://platform.openai.com/api-keys)

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/MuhammadMaazA/AgentForge.git
    cd AgentForge
    ```

2.  **Set up the Backend:**
    ```bash
    # Navigate to the backend directory
    cd backend

    # Create and activate a virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`

    # Install dependencies
    pip install -r requirements.txt

    # Create an environment file from the example
    cp .env.example .env
    ```
    Now, open `backend/.env` with a text editor and add your `OPENAI_API_KEY`.

3.  **Set up the Frontend:**
    ```bash
    # Navigate to the frontend directory from the root
    cd ../frontend

    # Install dependencies
    npm install
    ```

### Running the Application

You need to run the frontend and backend in two separate terminal windows.

-   **Terminal 1: Run the Backend**
    ```bash
    # Make sure you are in the 'backend' directory and your venv is active
    uvicorn main:app --reload
    ```
    Your backend will be running at `http://127.0.0.1:8000`.

-   **Terminal 2: Run the Frontend**
    ```bash
    # Make sure you are in the 'frontend' directory
    npm run dev
    ```
    Your frontend will be running at `http://localhost:3000`. Open this URL in your browser!

---

## 🗺️ Future Roadmap

This project is the foundation for a much larger vision. Here are the next steps:

-   [ ] **Multi-File Generation:** Upgrade the AI prompt to generate a full file structure (e.g., `app.py`, `utils.py`, `requirements.txt`) as a JSON object.
-   [ ] **Integrated IDE:** Replace the simple code display with a Monaco Editor instance and a file tree to create a true IDE experience.
-   [ ] **One-Click Run:** Use Docker to create a secure sandbox environment where users can execute the generated code directly from the UI.
-   [ ] **Vector DB Integration:** Add options for RAG (Retrieval-Augmented Generation) to allow agents to work with user-provided documents.
-   [ ] **User Accounts & Deployment:** Add user authentication to save projects and one-click deployment options to services like Vercel and Render.

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. If you have ideas for features or improvements, please open an issue to discuss what you would like to change.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
