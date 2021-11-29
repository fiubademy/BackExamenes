from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://fwvgbztmprfrsw:4ebcc733023c58076b68c792d8d918de53b41869d659cb729ab1408bc7658c11@ec2-44-198-29-193.compute-1.amazonaws.com:5432/dmkfrcjs45li0"
engine = create_engine(DATABASE_URL)

Base = declarative_base()

TEST_DATABASE_URL = "postgresql://vfvppkkitwcptw:c3f1b208b34853f99b260c9505598bd4aea14f0cec9c55b049a6b66c2f14cb4d@ec2-34-233-0-64.compute-1.amazonaws.com:5432/df2bgm4h0eg0je"
test_engine = create_engine(TEST_DATABASE_URL)