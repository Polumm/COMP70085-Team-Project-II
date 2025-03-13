# MovieMe: Movie Social Platform

## Overview
MovieMe is a web-based social platform that enriches the experience of discovering and sharing movies through social interactions. The platform serves as both a personal movie catalog system and a movie-centric social network. 

- **Please review the refactored and optimized microservices project, now with WebSocket real-time chat support and enhanced stateless JWT authentication**. [https://github.com/Polumm/demo-whatsapp]

## Key Features
- **User Authentication & Profiles:** Secure user accounts with personalized movie collections.
- **Social Connectivity:** Friend requests and friend-based movie recommendations.
- **Intelligent Chatbot:** Personalized movie recommendations using mood, genre preferences, and friends’ movie selections powered by Google Gemini API.
- **Advanced Movie Search:** Explore movies with extensive filtering using TMDB API.

## Architecture
- **Microservices:**
  - Main Application (Flask-based frontend)
  - Database Microservice (PostgreSQL, Redis caching)
  - Chatbot Microservice (Google Gemini API integration)

- **Hosting & Deployment:**
  - Azure Kubernetes Service (AKS) and Azure Container Instances (ACI)
  - Docker containerization for consistency
  - GitHub Actions for automated deployments

## Tech Stack
- **Frontend:** Flask (HTML/CSS/JavaScript), AJAX
- **Backend:** Python, PostgreSQL, Redis
- **Microservices:** Docker, Kubernetes, Azure
- **APIs:** TMDB, Google Gemini, Movie Quotes API

## Links
- **Web App:** [MovieMe](http://movie-me.uksouth.azurecontainer.io/)
- **Demo Video:** [Watch here](https://youtu.be/uJejTzyboFY)
- **Main App Repo:** [COMP70085-Team-Project-II](https://github.com/Polumm/COMP70085-Team-Project-II)
- **Database Microservice Repo:** [chatbot-database](https://github.com/Polumm/chatbot-database)
- **Chatbot Microservice Repo:** [chatbot-service](https://github.com/Polumm/chatbot-service)

## Performance & Scalability
- **Caching Strategy:** Redis for rapid data retrieval, fallback to PostgreSQL.
- **Scaling:** Kubernetes autoscaling to manage traffic (tested with 3000+ users).
- **Session Management:** Session affinity with cookie-based routing to maintain consistent user experience.

## Security & Privacy
- **Authentication:** JWT-based secure and stateless authentication.
- **API Security:** Strict input validation and secure decorator-based access control.

## Future Enhancements
- Improved chatbot natural language interactions.
- Movie soundtrack integration.
- Expanded social media-inspired features.
- Enhanced AI-driven personalized recommendations.

## Team Members
- Asal Shams
- Chujia Song
- Kevin Chave
- Sermila Ispartaligil
- Ziheng Shan

