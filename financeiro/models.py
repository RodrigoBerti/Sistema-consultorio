
from django.db import models
from django.core.validators import MinValueValidator
from pacientes.models import Paciente
from decimal import Decimal
from django.db.models import Sum


class ContaReceber(models.Model):
    class Tipo(models.TextChoices):
        PROCEDIMENTO = 'PROCEDIMENTO', 'Procedimento'
        TRATAMENTO = 'TRATAMENTO', 'Tratamento parcelado'

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        related_name='contas_receber'
    )
    tipo = models.CharField(
        max_length=20,
        choices=Tipo.choices
    )
    descricao = models.CharField(max_length=200)
    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    data_criacao = models.DateField(auto_now_add=True)
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ['-data_criacao']
        verbose_name = 'Conta a receber'
        verbose_name_plural = 'Contas a receber'

    def __str__(self):
        return f'{self.paciente.nome} - {self.descricao}'

    @property
    def total_recebido(self):
        return sum(
            (parcela.total_recebido for parcela in self.parcelas.all()),
            Decimal('0.00')
        )

    @property
    def saldo_devedor(self):
        return self.valor_total - self.total_recebido


class ParcelaReceber(models.Model):
    conta = models.ForeignKey(
        ContaReceber,
        on_delete=models.CASCADE,
        related_name='parcelas'
    )
    numero = models.PositiveIntegerField()
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    data_vencimento = models.DateField()

    class Meta:
        ordering = ['data_vencimento', 'numero']
        constraints = [
            models.UniqueConstraint(
                fields=['conta', 'numero'],
                name='parcela_numero_unico_por_conta'
            )
        ]
        verbose_name = 'Parcela a receber'
        verbose_name_plural = 'Parcelas a receber'

    def __str__(self):
        return f'Parcela {self.numero} - {self.conta.descricao}'

    @property
    def total_recebido(self):
        return self.recebimentos.filter(
            estornado=False
        ).aggregate(
            total=Sum('valor')
        )['total'] or Decimal('0.00')

    @property
    def saldo_devedor(self):
        return self.valor - self.total_recebido


class Recebimento(models.Model):

    estornado = models.BooleanField(default=False)
    data_estorno = models.DateField(null=True, blank=True)
    motivo_estorno = models.CharField(max_length=255, blank=True)

    class FormaPagamento(models.TextChoices):
        DINHEIRO = 'DINHEIRO', 'Dinheiro'
        PIX = 'PIX', 'PIX'
        DEBITO = 'DEBITO', 'Cartão de débito'
        CREDITO = 'CREDITO', 'Cartão de crédito'
        TRANSFERENCIA = 'TRANSFERENCIA', 'Transferência'
        OUTRO = 'OUTRO', 'Outro'

    parcela = models.ForeignKey(
        ParcelaReceber,
        on_delete=models.PROTECT,
        related_name='recebimentos'
    )
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    data_recebimento = models.DateField()
    forma_pagamento = models.CharField(
        max_length=20,
        choices=FormaPagamento.choices
    )
    observacoes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-data_recebimento']
        verbose_name = 'Recebimento'
        verbose_name_plural = 'Recebimentos'

    def __str__(self):
        return f'{self.parcela} - R$ {self.valor}'


class Despesa(models.Model):
    class Categoria(models.TextChoices):
        FIXA = 'FIXA', 'Despesa fixa'
        VARIAVEL = 'VARIAVEL', 'Despesa variável'

    descricao = models.CharField(max_length=200)
    categoria = models.CharField(
        max_length=10,
        choices=Categoria.choices
    )
    fornecedor = models.CharField(max_length=150, blank=True)
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    data_vencimento = models.DateField()
    recorrente = models.BooleanField(default=False)
    observacoes = models.TextField(blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data_vencimento']
        verbose_name = 'Despesa'
        verbose_name_plural = 'Despesas'

    def __str__(self):
        return self.descricao

    @property
    def total_pago(self):
        return sum(
            pagamento.valor
            for pagamento in self.pagamentos.all()
        )

    @property
    def saldo_devedor(self):
        return self.valor - self.total_pago


class PagamentoDespesa(models.Model):
    class FormaPagamento(models.TextChoices):
        DINHEIRO = 'DINHEIRO', 'Dinheiro'
        PIX = 'PIX', 'PIX'
        DEBITO = 'DEBITO', 'Cartão de débito'
        CREDITO = 'CREDITO', 'Cartão de crédito'
        TRANSFERENCIA = 'TRANSFERENCIA', 'Transferência'
        BOLETO = 'BOLETO', 'Boleto'
        OUTRO = 'OUTRO', 'Outro'

    despesa = models.ForeignKey(
        Despesa,
        on_delete=models.PROTECT,
        related_name='pagamentos'
    )
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    data_pagamento = models.DateField()
    forma_pagamento = models.CharField(
        max_length=20,
        choices=FormaPagamento.choices
    )
    observacoes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-data_pagamento']
        verbose_name = 'Pagamento de despesa'
        verbose_name_plural = 'Pagamentos de despesas'

    def __str__(self):
        return f'{self.despesa.descricao} - R$ {self.valor}'
