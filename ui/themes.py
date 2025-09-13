#!/usr/bin/env python3
"""
Sistema de temas para o PDF Merger App
Gerencia cores e estilos para modo claro e escuro
"""

from enum import Enum
from typing import Dict, Any

class ThemeMode(Enum):
    """Modos de tema disponíveis"""
    LIGHT = "light"
    DARK = "dark"

class ThemeManager:
    """Gerenciador de temas da aplicação"""
    
    def __init__(self, initial_mode: ThemeMode = ThemeMode.LIGHT):
        self.current_mode = initial_mode
        self._themes = self._initialize_themes()
    
    def _initialize_themes(self) -> Dict[ThemeMode, Dict[str, str]]:
        """Inicializa os temas disponíveis"""
        return {
            ThemeMode.LIGHT: {
                'bg_primary': '#FAFBFC',
                'bg_secondary': '#F4F6F8',
                'bg_tertiary': '#EBEDEF',
                'text_primary': '#1C1E21',
                'text_secondary': '#606770',
                'accent_blue': '#E8F4F8',
                'accent_blue_hover': '#D1E7ED',
                'accent_red': '#FDF2F2',
                'accent_red_hover': '#FAE1E1',
                'accent_purple': '#F7F3FF',
                'accent_purple_hover': '#EDE7FF',
                'border': '#DDE1E5',
                'selected': '#E8F4F8',
                'progress_color': '#1877F2',
                'error_color': '#E74C3C',
                'success_color': '#2ECC71',
                'warning_color': '#F39C12'
            },
            ThemeMode.DARK: {
                'bg_primary': '#0D1117',
                'bg_secondary': '#161B22',
                'bg_tertiary': '#21262D',
                'text_primary': '#F0F6FC',
                'text_secondary': '#8B949E',
                'accent_blue': '#0D2138',
                'accent_blue_hover': '#1A2B42',
                'accent_red': '#2D1417',
                'accent_red_hover': '#3C1E23',
                'accent_purple': '#2D1B44',
                'accent_purple_hover': '#3E2759',
                'border': '#30363D',
                'selected': '#1F6FEB',
                'progress_color': '#58A6FF',
                'error_color': '#F85149',
                'success_color': '#56D364',
                'warning_color': '#E3B341'
            }
        }
    
    @property
    def is_dark_mode(self) -> bool:
        """Retorna True se está em modo escuro"""
        return self.current_mode == ThemeMode.DARK
    
    def get_colors(self) -> Dict[str, str]:
        """Retorna as cores do tema atual"""
        return self._themes[self.current_mode].copy()
    
    def get_color(self, color_name: str) -> str:
        """Retorna uma cor específica do tema atual"""
        colors = self.get_colors()
        return colors.get(color_name, '#000000')
    
    def toggle_theme(self) -> ThemeMode:
        """Alterna entre temas claro e escuro"""
        if self.current_mode == ThemeMode.LIGHT:
            self.current_mode = ThemeMode.DARK
        else:
            self.current_mode = ThemeMode.LIGHT
        return self.current_mode
    
    def set_theme(self, mode: ThemeMode):
        """Define o tema atual"""
        if mode in self._themes:
            self.current_mode = mode
    
    def get_button_colors(self, button_type: str = 'primary') -> Dict[str, str]:
        """Retorna cores específicas para botões"""
        colors = self.get_colors()
        
        # Cor do texto dos botões sempre preta para melhor contraste
        text_color = '#000000'
        
        button_configs = {
            'primary': {
                'bg': colors['accent_blue'],
                'fg': text_color,
                'hover_bg': colors['accent_blue_hover']
            },
            'danger': {
                'bg': colors['accent_red'], 
                'fg': text_color,
                'hover_bg': colors['accent_red_hover']
            },
            'secondary': {
                'bg': colors['accent_purple'],
                'fg': text_color, 
                'hover_bg': colors['accent_purple_hover']
            }
        }
        
        return button_configs.get(button_type, button_configs['primary'])
    
    def get_hover_color_map(self) -> Dict[str, str]:
        """Retorna mapeamento de cores para efeitos hover"""
        colors = self.get_colors()
        
        if self.is_dark_mode:
            return {
                colors['accent_blue']: colors['accent_blue_hover'],
                colors['accent_red']: colors['accent_red_hover'], 
                colors['accent_purple']: colors['accent_purple_hover']
            }
        else:
            return {
                '#E3F2FD': '#BBDEFB',  # Azul claro -> mais escuro
                '#FFEBEE': '#FFCDD2',  # Rosa claro -> mais escuro  
                '#F3E5F5': '#E1BEE7',  # Roxo claro -> mais escuro
                '#0078D4': '#106EBE',  # Azul escuro -> mais escuro
                '#D13438': '#B71C1C',  # Vermelho escuro -> mais escuro
                '#8B5CF6': '#7C3AED',  # Roxo escuro -> mais escuro
                '#1d272e': '#2a3940',  # Cor específica -> mais claro
            }
    
    def apply_to_widget(self, widget, color_keys: Dict[str, str]):
        """Aplica cores do tema atual a um widget"""
        colors = self.get_colors()
        config = {}
        
        for config_key, color_key in color_keys.items():
            if color_key in colors:
                config[config_key] = colors[color_key]
        
        widget.config(**config)
