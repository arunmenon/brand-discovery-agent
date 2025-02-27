from setuptools import setup, find_packages

setup(
    name="counterfeit_detector",
    version="0.1.0",
    description="A system for detecting counterfeit products using multi-modal LLMs and brand knowledge graphs",
    author="Brand Discovery Team",
    packages=find_packages(),
    install_requires=[
        "crewai>=0.28.0",
        "openai>=1.3.0",
        "neo4j>=5.14.0",
        "python-dotenv>=1.0.0",
        "pytest>=7.4.0",
        "concurrent-log-handler>=0.9.24",
        "tenacity>=8.2.3"
    ],
    python_requires=">=3.9",
)