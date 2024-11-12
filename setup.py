from setuptools import setup, find_packages

setup(
    name="fieldsurveys",
    version="1.0.3",
    author="Karan Gathani",
    author_email="karan.gathani+fieldsurveysapp@posit.co",
    packages=find_packages(),
    description="A Python package for creating and managing field surveys.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/karangattu/fieldsurveys",
    include_package_data=True,
    package_data={"fieldsurveys": ["*"]},
    entry_points={"console_scripts": ["fieldsurveys = fieldsurveys:copy_app_files"]},
    setup_requires=["wheel"],
    install_requires=[
        "beautifulsoup4==4.12.3",
        "cryptography==43.0.1",
        "faicons==0.2.2",
        "geopy==2.4.1",
        "gspread==6.1.2",
        "gspread-dataframe==4.0.0",
        "htmltools==0.5.3",
        "pandas==2.2.3",
        "plotly==5.24.1", 
        "pytz==2024.2",
        "PyYAML==6.0.2",
        "requests==2.32.3",
        "rsconnect_python==1.24.0",
        "shiny==1.1.0",
        "shinyswatch==0.7.0",
        "timezonefinder==6.5.3",
        "us==3.2.0",
        "Wikipedia-API==0.7.1",
        "google-api-python-client==2.151.0"
    ],
    extras_require={
        "tests": [
            "playwright==1.47.0",
            "pytest==8.3.3",
            "pytest-mock==3.14.0",
            "pytest-playwright==0.5.2",
        ]
    },
)
