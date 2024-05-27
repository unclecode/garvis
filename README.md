# Garvis (Starts with G) 🌟

## This README is a work in progress. Please check back soon for more information. 🔧

Welcome to Garvis! 🎉 This project leverages the speech-to-text endpoint from Groq, utilizing their cutting-edge LPU (Language Processing Unit) chips, which offer unprecedented speed, faster than traditional GPUs. The goal of Garvis is to provide a near real-time user experience by chunking based on silence and translating instantly, thanks to the high-speed capabilities of Groq's hardware and the LLAMA3 large language model. 🚀

## Attention: 🚨

At the moment, Groq API is free but has a limited rate. The techniques I'm using to create real-time results require multiple calls, so you may reach your rate limit quickly. Just keep this in mind. ⏳

## Features

- **Real-Time Translation**: By chunking input based on silence, Garvis can translate in near real-time, providing an almost instantaneous user experience. ⏱️
- **Asynchronous Core Library**: The core of Garvis, named "garvis", is built to be asynchronous, making it adaptable to various user interfaces. 🌐
- **Flexible User Interface**: Garvis is designed to be user interface agnostic, allowing it to be integrated into any platform. Currently, there are examples for both a desktop application and a terminal interface. 💻🖥️

## Repository Structure 📁

- **examples/**: Contains example implementations of Garvis.
  - **desktop/**: A simple desktop application showcasing Garvis in action. 🖥️
  - **terminal/**: A sample of using the Garvis library in a terminal environment. 🖥️

## Getting Started 🚀

### Prerequisites 📋

- Python 3.x 🐍
- Dependencies listed in `requirements.txt`

### Installation 💻

1. Clone the repository:
```
git clone https://github.com/unclecode/garvis.git
cd garvis
```

2. Install the required dependencies:
```
pip install -r requirements.txt
```

### Usage 🚀

#### Core Library 📚

[This part is a work in progress. Please check back soon for more information.] 🔧

#### Desktop Application 🖥️

Navigate to the `examples/desktop` directory and run the application:

```
cd examples/desktop
python garvis_app_async.py
```

#### Terminal Application 💻

Navigate to the `examples/terminal` directory and run the terminal example:

```
cd examples/terminal
python terminal_ui_async.py
```

## Contributing 🤝

Contributions are welcome! If you have suggestions for improvements or encounter any issues, please feel free to open an issue or submit a pull request. 🛠️

## License 📜

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 📄

## Acknowledgements 🙏

- [Groq](https://www.groq.com) for their Speciatex endpoint and LPU chips. 💡
- The developers of the LLAMA3 large language model. 🧠

## Contact 📬

- X (UncleCode) - [@unclecode](https://x.com/unclecode) 📱

---

Thank you for checking out Garvis! Stay tuned for more updates and examples. 🌟
