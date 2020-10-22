import os

class Config:
    #SECRET_KEY = os.environ.get('SECRET_KEY') #change it to some key after that add this variable to environment
    SQLALCHEMY_DATABASE_URI = 'sqlite:///trafficdatabase.db'#os.environ.get('SQLALCHEMY_DATABASE_URI') #This also reads from the environment can be hardcoded
