import sys
from sqlalchemy import Column, Date, ForeignKey, Integer, String, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine


Base = declarative_base()



class User(Base):
    """
    Basic User information table

    Attributes:
        attr1 (str): user's name
        attr2 (str): user's email
        attr3 (str): user's picture
        attr4 (int): user's unique id
    """

    __tablename__ = 'user'

    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    id = Column(Integer, primary_key=True)


class Category(Base):
    """
    Category table

    Attributes:
        attr1 (int): unique id
        attr2 (str): category name
        attr3 (int): ForeignKey for user.id
        attr4 (relationship): User
    """

    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Returns object data in easily serializeable format"""
        return {
            'name': self.name
        }


class Quote(Base):
    """
    Quote table

    Attributes:
        attr2 (str): name of the author
        attr3 (int): unique id
        attr4 (str): quote
        attr5 (date): created on date
        attr6 (int): ForeignKey for category.id
        attr7 (relationship): category
        attr8 (int): ForeignKey for user.id
        attr9 (relationship): User
    """

    __tablename__ = 'quote'

    author = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(450))
    created_on = Column(Date, default=func.now())
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Returns object data in easily serializeable format"""
        return {
            'author': self.author,
            'description': self.description,
            'created on': self.created_on,
            'id': self.id
        }


engine = create_engine('sqlite:///quotes.db')
Base.metadata.create_all(engine)
