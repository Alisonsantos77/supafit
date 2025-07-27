"""
Módulo de validações para a aplicação SupaFit
"""

import re
from typing import Tuple, Optional


class ValidationResult:
    """Classe para encapsular resultados de validação"""

    def __init__(self, is_valid: bool, message: str = ""):
        self.is_valid = is_valid
        self.message = message


class Validators:
    """Classe com métodos estáticos para validações diversas"""

    @staticmethod
    def validate_email(email: str) -> ValidationResult:
        """
        Valida formato de email

        Args:
            email (str): Email a ser validado

        Returns:
            ValidationResult: Resultado da validação
        """
        if not email or not email.strip():
            return ValidationResult(False, "Email é obrigatório")

        email = email.strip()
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if not re.match(email_pattern, email):
            return ValidationResult(
                False, "Email inválido! Use o formato: nome@dominio.com"
            )

        return ValidationResult(True, "Email válido")

    @staticmethod
    def validate_password(password: str) -> ValidationResult:
        """
        Valida senha com critérios de segurança

        Args:
            password (str): Senha a ser validada

        Returns:
            ValidationResult: Resultado da validação
        """
        if not password:
            return ValidationResult(False, "Senha é obrigatória")

        if len(password) < 6:
            return ValidationResult(False, "A senha deve ter pelo menos 6 caracteres")

        # Verificações adicionais de segurança
        if len(password) < 8:
            return ValidationResult(
                True, "Senha aceitável, mas recomendamos pelo menos 8 caracteres"
            )

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)

        if not (has_upper and has_lower and has_digit):
            return ValidationResult(
                True,
                "Senha aceitável, mas recomendamos incluir maiúsculas, minúsculas e números",
            )

        return ValidationResult(True, "Senha forte")

    @staticmethod
    def validate_password_confirmation(
        password: str, confirmation: str
    ) -> ValidationResult:
        """
        Valida se a confirmação de senha coincide com a senha original

        Args:
            password (str): Senha original
            confirmation (str): Confirmação da senha

        Returns:
            ValidationResult: Resultado da validação
        """
        if not confirmation:
            return ValidationResult(False, "Confirmação de senha é obrigatória")

        if password != confirmation:
            return ValidationResult(False, "As senhas não coincidem")

        return ValidationResult(True, "Senhas coincidem")

    @staticmethod
    def validate_fitness_level(level: str) -> ValidationResult:
        """
        Valida nível de fitness

        Args:
            level (str): Nível de fitness

        Returns:
            ValidationResult: Resultado da validação
        """
        valid_levels = ["iniciante", "intermediário", "avançado"]

        if not level or level not in valid_levels:
            return ValidationResult(False, "Selecione um nível de fitness válido")

        return ValidationResult(True, "Nível válido")

    @staticmethod
    def validate_terms_acceptance(accepted: bool) -> ValidationResult:
        """
        Valida se os termos foram aceitos

        Args:
            accepted (bool): Se os termos foram aceitos

        Returns:
            ValidationResult: Resultado da validação
        """
        if not accepted:
            return ValidationResult(
                False, "Você deve aceitar os Termos de Uso e Política de Privacidade"
            )

        return ValidationResult(True, "Termos aceitos")

    @staticmethod
    def validate_registration_form(
        email: str,
        password: str,
        password_confirmation: str,
        level: str,
        terms_accepted: bool,
    ) -> Tuple[bool, str]:
        """
        Valida todo o formulário de registro

        Args:
            email (str): Email do usuário
            password (str): Senha do usuário
            password_confirmation (str): Confirmação da senha
            level (str): Nível de fitness
            terms_accepted (bool): Se os termos foram aceitos

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        # Validar email
        email_result = Validators.validate_email(email)
        if not email_result.is_valid:
            return False, email_result.message

        # Validar senha
        password_result = Validators.validate_password(password)
        if not password_result.is_valid:
            return False, password_result.message

        # Validar confirmação de senha
        confirmation_result = Validators.validate_password_confirmation(
            password, password_confirmation
        )
        if not confirmation_result.is_valid:
            return False, confirmation_result.message

        # Validar nível
        level_result = Validators.validate_fitness_level(level)
        if not level_result.is_valid:
            return False, level_result.message

        # Validar termos
        terms_result = Validators.validate_terms_acceptance(terms_accepted)
        if not terms_result.is_valid:
            return False, terms_result.message

        return True, "Formulário válido"
