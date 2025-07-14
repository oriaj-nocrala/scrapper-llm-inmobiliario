"""
Interactive CLI for property questions using the RAG chain.
"""
import json
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from ..rag.property_rag_chain import (PropertyRAGChain,
                                      create_rag_chain_from_scraped_data)
from ..utils.config import settings

console = Console()


class PropertyChatCLI:
    """Interactive CLI for chatting about properties."""
    
    def __init__(self, rag_chain: PropertyRAGChain):
        """Initialize the chat CLI.
        
        Args:
            rag_chain: Configured RAG chain for property questions
        """
        self.rag_chain = rag_chain
        self.conversation_history = []
    
    def start_chat(self):
        """Start the interactive chat session."""
        console.print(Panel.fit(
            "[bold blue]🏠 Asistente de Propiedades AssetPlan[/bold blue]\n"
            "Pregúntame sobre propiedades disponibles. Escribe 'salir' para terminar.",
            style="blue"
        ))
        
        # Show system stats
        self._show_system_stats()
        
        console.print("\n[bold green]¡Listo! Puedes hacer preguntas sobre propiedades.[/bold green]\n")
        
        while True:
            try:
                # Get user question
                question = Prompt.ask("\n[bold cyan]Tu pregunta[/bold cyan]")
                
                if question.lower() in ['salir', 'quit', 'exit', 'bye']:
                    console.print("\n[bold yellow]¡Hasta luego! 👋[/bold yellow]")
                    break
                
                if question.lower() in ['help', 'ayuda']:
                    self._show_help()
                    continue
                
                if question.lower() in ['stats', 'estadisticas']:
                    self._show_system_stats()
                    continue
                
                # Process the question
                self._process_question(question)
                
            except KeyboardInterrupt:
                console.print("\n\n[bold yellow]¡Hasta luego! 👋[/bold yellow]")
                break
            except Exception as e:
                console.print(f"\n[bold red]Error: {e}[/bold red]")
    
    def _process_question(self, question: str):
        """Process a user question and display the response.
        
        Args:
            question: User's question
        """
        try:
            # Show processing indicator
            with console.status("[bold green]Procesando tu pregunta...") as status:
                answer = self.rag_chain.ask_question(question)
            
            # Store in conversation history
            self.conversation_history.append({
                "question": question,
                "answer": answer.model_dump()
            })
            
            # Display the answer
            self._display_answer(answer)
            
        except Exception as e:
            console.print(f"\n[bold red]Error procesando la pregunta: {e}[/bold red]")
    
    def _display_answer(self, answer):
        """Display the answer in a formatted way.
        
        Args:
            answer: PropertyAnswer object
        """
        # Main answer
        console.print(Panel(
            Markdown(answer.answer),
            title=f"[bold green]Respuesta[/bold green] (Confianza: {answer.confidence:.0%})",
            border_style="green"
        ))
        
        # Sources table if available
        if answer.sources:
            self._display_sources_table(answer.sources)
        
        # Query info
        console.print(f"\n[dim]Tipo de consulta: {answer.query_type} | "
                     f"Propiedades encontradas: {answer.property_count}[/dim]")
    
    def _display_sources_table(self, sources):
        """Display sources in a formatted table.
        
        Args:
            sources: List of source dictionaries
        """
        if not sources:
            return
        
        table = Table(title="📋 Fuentes consultadas", show_header=True, header_style="bold blue")
        table.add_column("Propiedad", style="cyan", no_wrap=True)
        table.add_column("Ubicación", style="green")
        table.add_column("Precio", style="yellow")
        table.add_column("Detalles", style="white")
        table.add_column("URL", style="blue", no_wrap=True)
        
        for source in sources[:5]:  # Limit to top 5 sources
            title = source.get("title", "N/A")[:30] + "..." if len(source.get("title", "")) > 30 else source.get("title", "N/A")
            location = source.get("location", "N/A")
            price = source.get("price_uf", source.get("price", "N/A"))
            
            details = []
            if source.get("area_m2"):
                details.append(f"{source['area_m2']}m²")
            if source.get("bedrooms"):
                details.append(f"{source['bedrooms']}d")
            if source.get("bathrooms"):
                details.append(f"{source['bathrooms']}b")
            
            details_str = " | ".join(details) if details else "N/A"
            
            url = source.get("url", "N/A")
            if len(url) > 30:
                url = url[:27] + "..."
            
            table.add_row(title, location, str(price), details_str, url)
        
        console.print("\n")
        console.print(table)
    
    def _show_system_stats(self):
        """Show system statistics."""
        try:
            stats = self.rag_chain.get_chain_stats()
            vector_stats = stats.get("vector_store_stats", {})
            
            stats_table = Table(title="📊 Estado del Sistema", show_header=False)
            stats_table.add_column("Métrica", style="cyan")
            stats_table.add_column("Valor", style="white")
            
            stats_table.add_row("Estado", vector_stats.get("status", "unknown"))
            stats_table.add_row("Propiedades indexadas", str(vector_stats.get("document_count", 0)))
            stats_table.add_row("Modelo LLM", stats.get("llm_model", "unknown"))
            stats_table.add_row("Documentos por consulta", str(stats.get("retrieval_k", 5)))
            
            # Property types
            prop_types = vector_stats.get("property_types", {})
            if prop_types:
                top_types = sorted(prop_types.items(), key=lambda x: x[1], reverse=True)[:3]
                types_str = ", ".join([f"{t}: {c}" for t, c in top_types])
                stats_table.add_row("Tipos principales", types_str)
            
            console.print("\n")
            console.print(stats_table)
            
        except Exception as e:
            console.print(f"[red]Error obteniendo estadísticas: {e}[/red]")
    
    def _show_help(self):
        """Show help information."""
        help_text = """
## 🏠 Comandos Disponibles

**Preguntas de ejemplo:**
- "¿Qué departamentos hay en Providencia bajo 3000 UF?"
- "Muéstrame casas con más de 3 dormitorios"
- "¿Cuáles son las propiedades más baratas?"
- "Recomiéndame algo en Las Condes"

**Comandos especiales:**
- `help` o `ayuda` - Mostrar esta ayuda
- `stats` o `estadisticas` - Mostrar estadísticas del sistema
- `salir` o `quit` - Terminar la sesión

**Tipos de consultas que puedo manejar:**
- Búsquedas específicas por ubicación, precio, características
- Comparaciones entre propiedades
- Recomendaciones personalizadas
- Información detallada de propiedades
"""
        console.print(Panel(Markdown(help_text), title="Ayuda", border_style="yellow"))
    
    def save_conversation(self, file_path: Optional[str] = None):
        """Save conversation history to file.
        
        Args:
            file_path: Path to save the conversation
        """
        if not self.conversation_history:
            console.print("[yellow]No hay conversación para guardar.[/yellow]")
            return
        
        if not file_path:
            timestamp = Path.cwd() / f"conversation_{len(self.conversation_history)}.json"
            file_path = str(timestamp)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
            
            console.print(f"[green]Conversación guardada en: {file_path}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error guardando conversación: {e}[/red]")


def main():
    """Main CLI entry point."""
    try:
        # Check if we have scraped data
        properties_file = Path(settings.properties_json_path)
        if not properties_file.exists():
            console.print(Panel(
                "[bold red]No se encontraron datos de propiedades.[/bold red]\n\n"
                f"Ejecuta primero el scraper para obtener datos:\n"
                f"[bold cyan]python -m src.scraper.professional_scraper[/bold cyan]\n\n"
                f"O verifica que existe el archivo: {properties_file}",
                title="Error",
                border_style="red"
            ))
            sys.exit(1)
        
        # Initialize RAG chain
        console.print("[bold blue]Inicializando sistema RAG...[/bold blue]")
        
        with console.status("[bold green]Cargando embeddings y modelo..."):
            rag_chain = create_rag_chain_from_scraped_data()
        
        # Start chat interface
        chat_cli = PropertyChatCLI(rag_chain)
        chat_cli.start_chat()
        
        # Ask if user wants to save conversation
        if chat_cli.conversation_history:
            save = Prompt.ask("\n¿Quieres guardar la conversación?", choices=["si", "no"], default="no")
            if save.lower() == "si":
                chat_cli.save_conversation()
    
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Operación cancelada por el usuario.[/bold yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Error fatal: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()