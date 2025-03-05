# core/dependency_injection.py

"""
A lightweight dependency injection container for the Nyx codebase.
This pattern allows for better testability and decoupling of components.
"""

import inspect
from typing import Dict, Any, Type, Callable, Optional, Set, get_type_hints

class ServiceContainer:
    """A simple dependency injection container."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Set[str] = set()
    
    def register(self, name: str, instance: Any = None, factory: Callable = None, 
                singleton: bool = False) -> None:
        """
        Register a service with the container.
        
        Args:
            name: The name to register the service under
            instance: An instance of the service (optional)
            factory: A factory function that creates the service (optional)
            singleton: Whether the service should be a singleton
        
        Either instance or factory must be provided, but not both.
        """
        if instance is not None and factory is not None:
            raise ValueError("Cannot provide both instance and factory")
        
        if instance is not None:
            self._services[name] = instance
        elif factory is not None:
            self._factories[name] = factory
            if singleton:
                self._singletons.add(name)
        else:
            raise ValueError("Must provide either instance or factory")
    
    def register_class(self, cls: Type, name: Optional[str] = None, 
                      singleton: bool = False) -> None:
        """
        Register a class with the container.
        
        Args:
            cls: The class to register
            name: The name to register the class under (defaults to class name)
            singleton: Whether the class should be a singleton
        """
        class_name = name or cls.__name__
        
        # Create a factory that handles dependency injection
        def factory():
            # Get the constructor parameters
            params = {}
            for param_name, param_type in get_type_hints(cls.__init__).items():
                if param_name != 'return' and param_name != 'self':
                    # Try to resolve the parameter from the container
                    if param_name in self._services or param_name in self._factories:
                        params[param_name] = self.resolve(param_name)
            
            # Create an instance with resolved parameters
            return cls(**params)
        
        self.register(class_name, factory=factory, singleton=singleton)
    
    def resolve(self, name: str) -> Any:
        """
        Resolve a service from the container.
        
        Args:
            name: The name of the service to resolve
            
        Returns:
            The resolved service
        """
        # Return the service if it's already instantiated
        if name in self._services:
            return self._services[name]
        
        # Use the factory to create the service
        if name in self._factories:
            instance = self._factories[name]()
            
            # Store the instance if it's a singleton
            if name in self._singletons:
                self._services[name] = instance
            
            return instance
        
        raise KeyError(f"Service '{name}' not registered")
    
    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()

# Create a global container
container = ServiceContainer()

# Helper functions to make usage more convenient
def register(name: str, instance: Any = None, factory: Callable = None, 
            singleton: bool = False) -> None:
    """Register a service with the global container."""
    container.register(name, instance, factory, singleton)

def register_class(cls: Type, name: Optional[str] = None, singleton: bool = False) -> None:
    """Register a class with the global container."""
    container.register_class(cls, name, singleton)

def resolve(name: str) -> Any:
    """Resolve a service from the global container."""
    return container.resolve(name)

def clear() -> None:
    """Clear all registered services from the global container."""
    container.clear()

# Example usage
if __name__ == "__main__":
    # Define a simple service class
    class Database:
        def __init__(self, connection_string: str):
            self.connection_string = connection_string
        
        def connect(self):
            print(f"Connecting to {self.connection_string}")
    
    # Define a dependent service
    class UserRepository:
        def __init__(self, database: Database):
            self.database = database
        
        def get_users(self):
            self.database.connect()
            return ["user1", "user2"]
    
    # Set up the container
    register("connection_string", instance="sqlite:///nyx.db")
    register("database", factory=lambda: Database(resolve("connection_string")), singleton=True)
    register_class(UserRepository, singleton=True)
    
    # Resolve the services
    user_repo = resolve("UserRepository")
    users = user_repo.get_users()
    print(f"Users: {users}")
