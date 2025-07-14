#!/usr/bin/env python3
"""
Utilidades comunes para análisis de código.
Funciones compartidas entre diferentes analizadores.
"""
import ast
from typing import Union

def calculate_complexity(node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]) -> int:
    """
    Calcular complejidad ciclomática de un nodo AST.
    
    Args:
        node: Nodo AST (función, clase, etc.)
        
    Returns:
        Complejidad ciclomática (mínimo 1)
    """
    complexity = 1  # Base complexity
    
    for child in ast.walk(node):
        # Decision points increase complexity
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            complexity += 1
        elif isinstance(child, (ast.ExceptHandler, ast.Try)):
            complexity += 1
        elif isinstance(child, (ast.BoolOp, ast.Compare)):
            complexity += 1
    
    return complexity

def normalize_code_for_comparison(code: str) -> str:
    """
    Normalizar código para comparación de duplicados.
    
    Args:
        code: Código fuente
        
    Returns:
        Código normalizado
    """
    lines = []
    for line in code.split('\n'):
        # Remover comentarios
        if '#' in line:
            line = line[:line.index('#')]
        # Normalizar espacios pero mantener indentación relativa
        stripped = line.strip()
        if stripped:
            # Contar indentación
            indent_level = (len(line) - len(line.lstrip())) // 4
            normalized_line = '    ' * indent_level + ' '.join(stripped.split())
            lines.append(normalized_line)
    
    return '\n'.join(lines)

def extract_function_signature(node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> str:
    """
    Extraer signatura de función para comparación.
    
    Args:
        node: Nodo de función AST
        
    Returns:
        Signatura normalizada
    """
    args = []
    for arg in node.args.args:
        args.append(arg.arg)
    
    return f"{node.name}({', '.join(args)})"

def is_similar_function(func1: dict, func2: dict, threshold: float = 0.8) -> bool:
    """
    Determinar si dos funciones son similares.
    
    Args:
        func1: Datos de primera función
        func2: Datos de segunda función 
        threshold: Umbral de similitud
        
    Returns:
        True si son similares
    """
    from difflib import SequenceMatcher
    
    similarity = SequenceMatcher(
        None, 
        func1.get('normalized', ''), 
        func2.get('normalized', '')
    ).ratio()
    
    return similarity >= threshold