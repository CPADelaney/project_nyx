# knowledge/acquisition.py

import os
import json
import sqlite3
import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup
import chromadb
from core.log_manager import initialize_log_db, LOG_DB

# Initialize vector DB for knowledge storage
client = chromadb.PersistentClient(path="./knowledge_store")
knowledge_collection = client.get_or_create_collection(name="learned_concepts")

class KnowledgeAcquisition:
    """Acquires new knowledge from various sources and integrates it into the AI's knowledge base."""

    def __init__(self):
        initialize_log_db()
        self._initialize_database()
        
    def _initialize_database(self):
        """Creates tables for knowledge tracking."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS knowledge_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_type TEXT,
                    source_url TEXT,
                    access_time TIMESTAMP,
                    status TEXT
                )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS knowledge_concepts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    concept TEXT,
                    description TEXT,
                    source_id INTEGER,
                    confidence REAL,
                    acquisition_time TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES knowledge_sources(id)
                )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS knowledge_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    concept1_id INTEGER,
                    concept2_id INTEGER,
                    relationship_type TEXT,
                    confidence REAL,
                    FOREIGN KEY (concept1_id) REFERENCES knowledge_concepts(id),
                    FOREIGN KEY (concept2_id) REFERENCES knowledge_concepts(id)
                )''')
        conn.commit()
        conn.close()

    def acquire_from_web(self, url, topic):
        """Extracts knowledge from web content."""
        try:
            # Log the source
            conn = sqlite3.connect(LOG_DB)
            c = conn.cursor()
            c.execute("INSERT INTO knowledge_sources (source_type, source_url, access_time, status) VALUES (?, ?, datetime('now'), ?)",
                     ("web", url, "processing"))
            source_id = c.lastrowid
            conn.commit()
            conn.close()
            
            # Fetch the content
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract main text and remove boilerplate
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            
            if not main_content:
                raise ValueError("Could not identify main content")
                
            # Extract paragraphs of content
            paragraphs = main_content.find_all('p')
            content = "\n".join([p.get_text() for p in paragraphs])
            
            # Extract key concepts (simplified)
            concepts = self._extract_concepts(content, topic)
            
            # Store in vector database
            for i, concept in enumerate(concepts):
                knowledge_collection.add(
                    documents=[concept["description"]],
                    metadatas=[{"concept": concept["concept"], "source": url, "confidence": concept["confidence"]}],
                    ids=[f"{topic}-{i}-{datetime.now().strftime('%Y%m%d%H%M%S')}"]
                )
                
                # Also store in SQL for relationships
                conn = sqlite3.connect(LOG_DB)
                c = conn.cursor()
                c.execute("INSERT INTO knowledge_concepts (concept, description, source_id, confidence, acquisition_time) VALUES (?, ?, ?, ?, datetime('now'))",
                         (concept["concept"], concept["description"], source_id, concept["confidence"]))
                concept_id = c.lastrowid
                
                # Update source status
                c.execute("UPDATE knowledge_sources SET status = ? WHERE id = ?", ("completed", source_id))
                conn.commit()
                conn.close()
                
            return concepts
                
        except Exception as e:
            print(f"Error acquiring knowledge: {str(e)}")
            
            # Log the failure
            conn = sqlite3.connect(LOG_DB)
            c = conn.cursor()
            c.execute("UPDATE knowledge_sources SET status = ? WHERE id = ?", (f"failed: {str(e)}", source_id))
            conn.commit()
            conn.close()
            
            return []
            
    def _extract_concepts(self, text, topic):
        """Extract key concepts from text (simplified version)."""
        # In a real implementation, this would use more sophisticated NLP
        concepts = []
        
        # Basic keyword extraction (would be improved with NLP)
        lines = text.split('\n')
        
        for line in lines:
            if len(line.strip()) < 20:  # Skip short lines
                continue
                
            # Look for definitional patterns
            definition_patterns = [
                r'([A-Z][a-zA-Z\s]+) is (.*?\.)',
                r'([A-Z][a-zA-Z\s]+) are (.*?\.)',
                r'([A-Z][a-zA-Z\s]+) refers to (.*?\.)',
                r'([A-Z][a-zA-Z\s]+) can be defined as (.*?\.)'
            ]
            
            for pattern in definition_patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    if len(match) >= 2:
                        concept_name = match[0].strip()
                        description = match[1].strip()
                        
                        # Only include if relevant to our topic
                        if topic.lower() in concept_name.lower() or topic.lower() in description.lower():
                            concepts.append({
                                "concept": concept_name,
                                "description": description,
                                "confidence": 0.7  # Placeholder confidence
                            })
        
        return concepts
        
    def learn_from_code_repository(self, repo_url):
        """Learns from code in a repository."""
        # Implementation would use GitHub API or git clone
        pass
        
    def integrate_new_knowledge(self):
        """Integrates newly acquired knowledge with existing knowledge."""
        # Retrieve all concepts
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT id, concept, description FROM knowledge_concepts")
        concepts = c.fetchall()
        
        # Find relationships between concepts
        for i, concept1 in enumerate(concepts):
            for concept2 in concepts[i+1:]:
                # Skip comparing a concept to itself
                if concept1[0] == concept2[0]:
                    continue
                    
                # Check for relationship based on common words (simplified)
                c1_words = set(concept1[2].lower().split())
                c2_words = set(concept2[2].lower().split())
                common_words = c1_words.intersection(c2_words)
                
                # If there are enough common significant words, create a relationship
                if len(common_words) >= 3:
                    relationship = "related"
                    confidence = min(1.0, len(common_words) / 10)
                    
                    c.execute("INSERT INTO knowledge_relationships (concept1_id, concept2_id, relationship_type, confidence) VALUES (?, ?, ?, ?)",
                             (concept1[0], concept2[0], relationship, confidence))
        
        conn.commit()
        conn.close()
        
    def query_knowledge(self, query, top_k=5):
        """Queries the knowledge base for relevant information."""
        results = knowledge_collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        return results

# Usage example
if __name__ == "__main__":
    knowledge_system = KnowledgeAcquisition()
    
    # Example: Learn about a topic from the web
    concepts = knowledge_system.acquire_from_web(
        "https://en.wikipedia.org/wiki/Artificial_general_intelligence",
        "AGI"
    )
    
    # Integrate the new knowledge
    knowledge_system.integrate_new_knowledge()
    
    # Query to test
    results = knowledge_system.query_knowledge("How is AGI different from narrow AI?")
    print(results)
