# 🤖 Offline AI Health Assistant

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](CONTRIBUTING.md)

A comprehensive, offline-first health assistant that provides symptom analysis, health monitoring, and educational resources. Built for low-resource environments with a focus on privacy and accessibility.

## 🌟 Features

### 🔍 Symptom Analysis
- Rule-based disease prediction using Jaccard similarity
- Multi-symptom input support
- Confidence scoring for predictions

### 🖥️ Multiple Interfaces
- Web-based dashboard
- Command-line interface (CLI)
- Voice command support (offline-capable)

### 📊 Health Monitoring
- Health data visualization
- Basic vitals tracking
- Historical data analysis

### 📚 Educational Resources
- Comprehensive drug reference database
- First aid guides
- Health education materials

### 🔒 Privacy-Focused
- 100% offline functionality
- No data collection
- Local data storage

## 🚀 Getting Started

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/sololito/Offline-AI-Health-Assistant.git
   cd offline-ai-health-assistant
   ```

2. Create and activate a virtual environment (recommended):

3. Install the Vosk model for voice recognition:
   - Download the Vosk model from: [Vosk Models](https://alphacephei.com/vosk/models)
   - Choose a model (e.g., "vosk-model-en-us-0.42-gigaspeech")
   - Extract the downloaded model folder
   - Place it in `voice_assistant/models/` directory
   - The final path should be: `voice_assistant/models/vosk-model-en-us-0.42-gigaspeech/`

4. Install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🏃‍♂️ Running the Application

### Web Interface
```bash
python web_app/app.py
```
Visit: [http://127.0.0.1:5000](http://127.0.0.1:5000)

### Command Line Interface
```bash
python src/main.py
```

## 📂 Project Structure

```
offline-ai-health-assistant/
│
├── analysis/                         # Health data analysis modules
│   ├── diagnosis_engine.py
│   └── vitals_analyzer.py
│
├── data/                             # Data storage and management
│   ├── health_diagnostics.csv
│   ├── drug_reference.json
│   ├── disease_symptom_database_300.csv
│
├── languages/                        # Localization files
│
├── output/                           # Generated reports and exports
│
├── sensors/                          # Hardware interfaces
│   ├── temperature_sensor.py
│   ├── bp_monitor.py
│   ├── glucose_meter.py
│   └── sensor_manager.py
│
├── src/                              # Core application logic
│   ├── main.py
│   ├── assistant.py
│   ├── symptom_matcher.py
│   ├── data_loader.py
│   └── utils.py
│
├── templates/                        # Web UI templates
│
├── voice_assistant/                  # Voice interface components
│   ├── recognizer.py
│   ├── speaker.py
│   ├── commands.py
│   └── models/
│       └── vosk-model-en
│
├── web_app/                          # Web application components
│
├── .env                              # Environment configuration
├── health_voice_interface.py         # Voice interface entry point
├── main.py                           # Main application entry point
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
├── Templates/web_app/
│   ├── app.py
│   ├── /templates/
│   │   ├── base.html
│   │   ├── diagnose.html
│   │   ├── diagnostic_center.html
│   │   ├── education_new.html
│   │   ├── education.html
│   │   ├── error.html  
│   │   ├── first_aid.html
│   │   ├── home.html
│   │   ├── index.html 
│   │   ├── login.html
│   │   └── upcoming.html
│   ├── /static/
│   │     └── style.css
│   └─/docs/
│        ├── educational/
│        │   ├── A Manual on Health Education in Primary Health Care.pdf  # General health education
│        │   ├── Child_and_Adolescent_Immunization_Schedule.pdf           # Vaccination/Prevention
│        │   ├── Decision_Making_Tool_for_Family-Planning.pdf            # Family Planning
│        │   ├── Maternal_and_Child_Nutrition.pdf                        # Nutrition/Maternal Health
│        │   ├── Nutrition_for_Every_Child.pdf                          # Nutrition/Child Health
│        │   └── family_planning.pdf                                    # Family Planning
│
├── requirements.txt
└── README.md
```

## 🛠️ Development

### Setting Up Development Environment
1. Fork the repository
2. Clone your fork
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Submit a pull request

### Running Tests
```bash
pytest tests/
```

## 📝 Data Format

### Symptom Database (CSV)
```csv
Disease,Symptoms
Influenza,fever,cough,headache
Malaria,fever,chills,sweating
Common Cold,sneezing,cough,runny nose
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to all contributors who have helped shape this project
- Built with ❤️ using Python and Flask
- Special thanks to the open-source community for their valuable tools and libraries

This project is open-source and licensed under the MIT License.

///////////////////////////////////////

## Inspiration

The **Offline AI Health Assistant** was inspired by a visit to a rural community where I witnessed how lack of internet access and medical personnel limited access to basic healthcare. The encounter highlighted the critical need for an offline solution that could empower individuals with timely and reliable health information, even in low-connectivity environments.

## What It Does

The assistant provides offline access to essential healthcare functionalities, including:

### Core Functionalities

- ✅ **Rule-based disease prediction** using Jaccard similarity  
- 🧠 **Personalized health recommendations and prescriptions**  
- 📚 **Health education resources**, including a searchable educational library  
- 🩺 **First aid guide** covering common incidents and emergencies  
- 🧾 **Health data analysis and visualization**  

### Offline and Device Compatibility

- 💾 **Complete offline functionality**, including local data storage with optional sync when online  
- 📱 **Lightweight interface** suitable for mobile phones and low-end devices like Raspberry Pi  
- 💡 **Responsive design** optimized for various screen sizes and device capabilities  

### Voice and Accessibility Features

- 🎙️ **Voice interaction** using offline speech recognition (supports limited commands)  
- 🗣️ **Accessible to non-literate and visually impaired users** through guided voice responses  

## How We Built It

The build followed a **phased approach**:

1. **Research**: Conducted a needs assessment and identified technical limitations  
2. **Prototyping**: Built the first version with a rule-based engine and offline web support  
3. **Development**: Added voice support, educational modules, and improved UI/UX  
4. **Testing**: Ran tests on low-end devices and with users in remote communities  

**Key technologies used**:

- `IndexedDB` for offline data  
- `PocketSphinx` for voice input  
- `Jaccard similarity` for symptom analysis  
- `Custom command parser` for offline interactions  

## Challenges We Ran Into

- Building accurate offline symptom analysis without internet-dependent AI  
- Achieving good voice recognition performance with local dialects  
- Syncing health records securely across offline and online environments  
- Ensuring smooth performance on low-end devices with limited memory  
- Creating a reliable user experience in rural, resource-constrained contexts  

## Accomplishments That We're Proud Of

- ✅ Developed a fully functional, offline-capable AI health assistant  
- 🌍 Enabled access to health guidance in low-connectivity regions  
- 🗣️ Designed voice support for users with low literacy or visual impairments  
- 📱 Built a responsive, lightweight app that runs on mobile and Raspberry Pi  
- 🔒 Created a system that respects privacy while enabling localized learning  

## What We Learned

- Offline-first health systems are not only feasible but **necessary**  
- Rule-based AI can be powerful when combined with community context  
- Voice technology must be inclusive and adapted to local languages  
- Continuous feedback from real users is vital to system improvement  
- Privacy and data sovereignty are crucial in health tech development  

## What's Next for Offline AI Health Assistant

We are now building the **next-generation version** of the Offline AI Health Assistant—a solar-powered, AI-integrated health monitoring system connected via a **LoRa-based mesh network** to enable real-time, offline community healthcare.

### 🔧 Key Upcoming Features

#### Solar-Powered Home Health Units
- Installed at individual homes  
- Allow symptom input via text or offline voice assistant  
- Include a “Send Urgent Need” button for emergency alerts with GPS, timestamp, and short message  

#### Offline Voice Assistance in Local Dialects
- Supports non-literate and visually impaired users  
- Guides users step-by-step through symptom checks and health advice  

#### LoRa Mesh Network
- Connects homes to a central medical base  
- Enables long-range, low-power, offline communication  
- Supports community-wide health updates and emergency alerts  

#### Continuous Learning Health Model
- Stores anonymized interaction data locally  
- Improves diagnostic accuracy over time  
- Syncs periodically via mobile health worker devices  

### 🚑 Mobile Medical Response Unit

- Equipped with diagnostic sensors and patient records  
- Responds in real-time to emergency alerts sent from homes  
- Staffed with trained medical professionals  

### 💻 Multi-Device Ecosystem

- **Desktop version** for clinics and schools  
- **Low-end version** for Raspberry Pi and constrained environments  
- **Mobile version** for smartphones used by health workers and community volunteers  



## Challenges We Faced

### 1. Technical Hurdles
- **Limited Device Capabilities**: Ensuring smooth performance on low-end devices with limited processing power and memory
- **Offline Data Management**: Implementing reliable local storage that works across different browsers and devices
- **Voice Recognition Accuracy**: Improving speech recognition in noisy environments common in rural settings
- **Data Synchronization**: Creating a robust sync system that handles intermittent connectivity gracefully

### 2. Healthcare-Specific Challenges
- **Medical Accuracy**: Ensuring all health information is accurate and evidence-based
- **Symptom Interpretation**: Handling variations in how users describe their symptoms
- **Emergency Handling**: Creating appropriate responses for potentially serious conditions
- **Multilingual Support**: Addressing language barriers in diverse communities

### 3. User Experience Challenges
- **Low-Literacy Users**: Designing an interface that works for users with varying literacy levels
- **Error Recovery**: Helping users recover from mistakes in voice or text input
- **Battery Optimization**: Minimizing power consumption for devices with limited battery life
- **Data Privacy**: Ensuring sensitive health information remains secure and private

### 4. Implementation Challenges
- **Cross-Platform Compatibility**: Making the app work consistently across different operating systems and devices
- **Performance Optimization**: Reducing app size and resource usage while maintaining functionality
- **Testing in Real Conditions**: Simulating low-connectivity environments for accurate testing
- **Documentation**: Creating clear, accessible documentation for both users and developers

### 5. Future Challenges
- **Expanding Medical Knowledge Base**: Keeping the medical information up-to-date
- **Adding More Languages**: Supporting additional languages and dialects
- **Integrating with Local Healthcare Systems**: Working with existing healthcare infrastructure
- **Scaling the Solution**: Making the system work for larger communities while maintaining performance
## 🛠️ Technologies Used

### Core Technologies
- **Backend**: Python 3.8+, Flask, SQLite
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, jQuery
- **Data Processing**: Pandas, NumPy, Jaccard Similarity
- **Voice Processing**: Vosk (with Kaldi), PyAudio, SoundDevice

### Development Tools
- **Version Control**: Git, GitHub
- **IDEs**: VS Code
- **Testing**: pytest, unittest, Selenium, Postman
- **Containerization**: Docker
- **CI/CD**: GitHub Actions, Dependabot

### Key Libraries & Dependencies
- **Web Framework**: Flask-Login, Flask-WTF, Flask-Migrate, Flask-CORS
- **Authentication**: PyJWT
- **Environment Management**: python-dotenv
- **Data Storage**: SQLite, IndexedDB, LocalStorage, SessionStorage

### Performance & Security
- **Performance**: Chrome DevTools, Lighthouse, gzip/brotli compression
- **Security**: Let's Encrypt, bcrypt, OWASP ZAP, bandit, safety
- **Accessibility**: WAI-ARIA, axe-core, NVDA screen reader testing

### Documentation & Quality
- **Documentation**: Markdown, Sphinx, reStructuredText, MkDocs
- **Code Quality**: pylint, black, mypy, flake8
- **Testing**: pytest, unittest, Selenium, Postman

### Localization & Internationalization
- gettext, Babel

### Data Visualization
- Chart.js, D3.js

### Offline Functionality
- Service Workers, Workbox, IndexedDB