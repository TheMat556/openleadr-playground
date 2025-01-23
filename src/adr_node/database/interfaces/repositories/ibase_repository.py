from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Any

T = TypeVar('T')
Q = TypeVar('Q')


# Base Repository Interface
class IBaseRepository(ABC, Generic[T, Q]):
  @abstractmethod
  def create(self, entity: T) -> T:
    """Create a single entity."""
    pass

  @abstractmethod
  def create_batch(self, entities: List[T]) -> List[T]:
    """Create multiple entities in batch."""
    pass

  @abstractmethod
  def read(self, id: Any) -> Optional[T]:
    """Read a single entity by its identifier."""
    pass

  @abstractmethod
  def read_all(self, query: Optional[Q] = None) -> List[T]:
    """Read all entities matching the query criteria."""
    pass

  @abstractmethod
  def update(self, entity: T) -> T:
    """Update an existing entity."""
    pass

  @abstractmethod
  def update_batch(self, entities: List[T]) -> List[T]:
    """Update multiple entities in batch."""
    pass

  @abstractmethod
  def delete(self, id: Any) -> bool:
    """Delete an entity by its identifier."""
    pass

  @abstractmethod
  def delete_batch(self, ids: List[Any]) -> bool:
    """Delete multiple entities by their identifiers."""
    pass
