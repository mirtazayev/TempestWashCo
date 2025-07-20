import datetime

from sqlalchemy import Column, Integer, String, DateTime

from database import Base


class Blog(Base):
    __tablename__ = "blogs"
    id: int = Column(Integer, primary_key=True, index=True)
    title: str = Column(String(255), index=True, nullable=False)
    content: str = Column(String(), nullable=False)
    updated_at: datetime.datetime = Column(DateTime(), default=datetime.datetime.utcnow,
                                           onupdate=datetime.datetime.utcnow)
    created_at: datetime.datetime = Column(DateTime(), default=datetime.datetime.utcnow)

    def __repr__(self) -> str:
        return f"Blog(id={self.id!r}, title={self.title!r}, content={self.content!r})"
