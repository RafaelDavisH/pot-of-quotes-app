import sys
from sqlalchemy import Column, Date, ForeignKey, Integer, String, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine


Base = declarative_base()


class User(Base):

    __tablename__ = 'user'

    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    id = Column(Integer, primary_key=True)


class Category(Base):

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
