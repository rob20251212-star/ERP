
import io
import os
import pandas as pd
from datetime import datetime, date
from flask import current_app
from sqlalchemy import func
from werkzeug.utils import secure_filename

from extensions import db
from models.cliente import Cliente
from models.vendedor import Vendedor
from models.materia_prima import MateriaPrima
from models.produto import ProdutoFinal
from models.venda import Venda, ContaReceber
from models.compra import Compra
from models.financeiro import Financeiro
from models.fornecedor import Fornecedor
from services.estoque_service import entrada_mp, atualizar_custo_medio
from services.financeiro_service import gerar_conta_receber, gerar_conta_pagar, lancar_receita, lancar_despesa
from services.custo_service import recalcular_custo_produto

ALLOWED_EXTENSIONS = {'xls', 'xlsx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def normalize_text(value):
    if value is None:
        return None
    if isinstance(value, str):
        result = value.strip()
        return result if result else None
    return str(value).strip()


def normalize_name(value):
    text = normalize_text(value)
    if not text:
        return None
    return ' '.join(text.split())


def parse_number(value, default=0.0):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if text == '':
        return default
    text = text.replace(' ', '')
    if ',' in text and '.' in text:
        text = text.replace('.', '').replace(',', '.')
    elif ',' in text:
        text = text.replace(',', '.')
    try:
        return float(text)
    except ValueError:
        return default


def parse_int(value, default=0):
    number = parse_number(value, default)
    try:
        return int(number)
    except (ValueError, TypeError):
        return default


def parse_date(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    try:
        parsed = pd.to_datetime(text, dayfirst=True, errors='coerce')
        if not pd.isna(parsed):
            return parsed.date()
    except Exception:
        pass
    return None


def find_header_row(rows, expected_keys):
    for idx, row in enumerate(rows[:12]):
        if not row:
            continue
        lower_row = [normalize_text(c).lower() if normalize_text(c) else '' for c in row]
        if any(key in cell for cell in lower_row for key in expected_keys):
            return idx, lower_row
    return None, None


def map_columns(lower_row):
    mapping = {}
    for index, cell in enumerate(lower_row):
        if not cell:
            continue
        if 'data' in cell and 'venda' not in cell and 'compra' not in cell:
            mapping.setdefault('data', index)
        if 'vendedor' in cell:
            mapping.setdefault('vendedor', index)
        if 'cliente' in cell:
            mapping.setdefault('cliente', index)
        if 'fornecedor' in cell:
            mapping.setdefault('fornecedor', index)
        if 'matéria' in cell or 'materia' in cell or 'produto' in cell:
            mapping.setdefault('materia_prima', index)
        if 'qtd' in cell or 'quantidade' in cell or 'sacos' in cell or 'qtde' in cell:
            mapping.setdefault('quantidade', index)
        if 'preço' in cell or 'preco' in cell:
            if 'unitario' in cell or 'unitário' in cell or 'unitario' in cell:
                mapping['preco_unitario'] = index
            else:
                mapping.setdefault('preco_unitario', index)
        if 'frete' in cell and 'tipo' not in cell:
            mapping.setdefault('frete', index)
        if 'tipo frete' in cell or 'tipo de frete' in cell:
            mapping.setdefault('tipo_frete', index)
        if 'desconto' in cell:
            mapping.setdefault('desconto', index)
        if 'total' in cell and 'total_com' not in mapping:
            mapping.setdefault('total', index)
        if 'nf' in cell or 'nota' in cell:
            mapping.setdefault('numero_nf', index)
        if 'prazo' in cell or 'vencimento' in cell:
            mapping.setdefault('prazo_pagamento', index)
        if 'forma' in cell and 'pagamento' in cell:
            mapping.setdefault('forma_pagamento', index)
        if 'obs' in cell or 'observ' in cell or 'descri' in cell:
            mapping.setdefault('observacoes', index)
    return mapping


def get_or_create_cliente(nome):
    nome = normalize_name(nome)
    if not nome:
        return None
    cliente = Cliente.query.filter(func.lower(Cliente.nome) == nome.lower()).first()
    if cliente:
        return cliente
    cliente = Cliente(nome=nome.title(), ativo=True)
    db.session.add(cliente)
    db.session.flush()
    return cliente


def get_or_create_vendedor(nome):
    nome = normalize_name(nome)
    if not nome:
        return None
    vendedor = Vendedor.query.filter(func.lower(Vendedor.nome) == nome.lower()).first()
    if vendedor:
        return vendedor
    vendedor = Vendedor(nome=nome.title(), ativo=True)
    db.session.add(vendedor)
    db.session.flush()
    return vendedor


def get_or_create_fornecedor(nome):
    nome = normalize_name(nome)
    if not nome:
        return None
    fornecedor = Fornecedor.query.filter(func.lower(Fornecedor.nome) == nome.lower()).first()
    if fornecedor:
        return fornecedor
    fornecedor = Fornecedor(nome=nome.upper(), tipo='outro', ativo=True)
    db.session.add(fornecedor)
    db.session.flush()
    return fornecedor


def get_or_create_materia_prima(nome):
    nome = normalize_name(nome)
    if not nome:
        return None
    materia = MateriaPrima.query.filter(func.lower(MateriaPrima.nome) == nome.lower()).first()
    if materia:
        return materia
    materia = MateriaPrima.query.filter(MateriaPrima.nome.ilike(f'%{nome}%')).first()
    if materia:
        return materia
    tipo = 'outro'
    lower = nome.lower()
    if 'celul' in lower:
        tipo = 'celulosico'
    elif 'celugel' in lower or 'gel' in lower:
        tipo = 'celugel'
    elif 'fibra' in lower:
        tipo = 'fibra'
    elif 'embal' in lower:
        tipo = 'embalagem'
    elif 'ades' in lower:
        tipo = 'adesivo'
    materia = MateriaPrima(
        nome=nome.title(),
        tipo=tipo,
        peso_saco_kg=25.0,
        quantidade_uso_kg=1.0,
        preco_saco=0.0,
        frete_saco=0.0,
        custo_medio=0.0,
        estoque_atual=0.0,
        estoque_minimo=0.0
    )
    db.session.add(materia)
    db.session.flush()
    return materia


def parse_rows_from_dataframe(rows):
    for row in rows:
        yield [None if (cell is None or (isinstance(cell, float) and pd.isna(cell))) else cell for cell in row]


def get_row_value(row, index):
    if index is None:
        return None
    if index < 0 or index >= len(row):
        return None
    return row[index]


def is_sales_sheet(sheet_name, lower_row):
    name = sheet_name.lower()
    if 'vendas' in name or 'sales' in name:
        return True
    if 'vendedor' in ' '.join(lower_row) and 'cliente' in ' '.join(lower_row):
        return True
    return False


def is_purchase_sheet(sheet_name, lower_row):
    name = sheet_name.lower()
    if 'compras' in name or 'purchase' in name:
        return True
    if 'fornecedor' in ' '.join(lower_row) and 'materia' in ' '.join(lower_row):
        return True
    return False


def parse_sales_rows(rows, summary, warnings):
    # This was the generic one, we can keep it as a fallback, or point to our custom parser.
    # To keep things clean, we will route sheet name matching to appropriate parsers in import_excel_planilha.
    pass


def parse_sales_sheet_custom(sheet_name, rows, summary, warnings):
    imported = 0
    blanks = 0
    produto = ProdutoFinal.query.first()
    custo_unitario = produto.custo_calculado if produto else 0.0
    
    for r_idx in range(3, len(rows)):
        row = rows[r_idx]
        if not row or all(c is None for c in row[:5]):
            blanks += 1
            if blanks > 15:
                break
            continue
        blanks = 0
        
        dt_val = row[0]
        if not dt_val:
            continue
        dt = parse_date(dt_val)
        if not dt:
            continue
            
        c_nome = row[2]
        if not c_nome:
            continue
        cliente = get_or_create_cliente(str(c_nome))
        if not cliente:
            continue
            
        qtd_celulose_paloma = row[3] if len(row) > 3 else None
        qtd_celulose_uchoa = row[4] if len(row) > 4 else None
        qtd_polimero = row[7] if len(row) > 7 else None
        
        qtd = 0
        preco_unit = 0.0
        vendedor_nome = row[1] if (len(row) > 1 and row[1]) else None
        
        if qtd_celulose_paloma is not None and isinstance(qtd_celulose_paloma, (int, float)) and qtd_celulose_paloma > 0:
            qtd = int(qtd_celulose_paloma)
            preco_unit = parse_number(row[5]) if len(row) > 5 else 0.0
            if not vendedor_nome:
                vendedor_nome = 'PALOMA'
        elif qtd_celulose_uchoa is not None and isinstance(qtd_celulose_uchoa, (int, float)) and qtd_celulose_uchoa > 0:
            qtd = int(qtd_celulose_uchoa)
            preco_unit = parse_number(row[5]) if len(row) > 5 else 0.0
            if not vendedor_nome:
                vendedor_nome = 'UCHOA'
        elif qtd_polimero is not None and isinstance(qtd_polimero, (int, float)) and qtd_polimero > 0:
            qtd = int(qtd_polimero)
            preco_unit = parse_number(row[8]) if len(row) > 8 else 0.0
            if not vendedor_nome:
                vendedor_nome = 'VENDEDOR'
                
        if qtd <= 0:
            continue
            
        vendedor = get_or_create_vendedor(vendedor_nome) if vendedor_nome else None
        desconto = parse_number(row[10]) if (len(row) > 10 and row[10] is not None) else 0.0
        
        total_val = row[11] if len(row) > 11 else None
        valor_liquido = parse_number(total_val) if total_val is not None else round(qtd * preco_unit - desconto, 2)
        if valor_liquido <= 0:
            valor_liquido = round(qtd * preco_unit - desconto, 2)
            
        forma_pag = row[19] if (len(row) > 19 and row[19]) else 'A VISTA'
        prazo = parse_int(row[20]) if (len(row) > 20 and row[20] is not None) else 0
        
        frete_val = row[21] if (len(row) > 21 and row[21]) else 'FOB'
        tipo_frete = 'CIF' if (isinstance(frete_val, str) and 'CIF' in frete_val.upper()) else 'FOB'
        obs = row[22] if (len(row) > 22 and row[22]) else None
        
        comm_pct = vendedor.comissao_pct if (vendedor and vendedor.comissao_pct) else 0.0
        comissao = round(valor_liquido * comm_pct / 100, 2)
        
        custo_total = round(custo_unitario * qtd, 2)
        lucro = round(valor_liquido - custo_total, 2)
        margem = round((lucro / valor_liquido * 100) if valor_liquido else 0, 2)
        
        devendo_val = row[13] if len(row) > 13 else 0
        status_pag = 'pago'
        if devendo_val and isinstance(devendo_val, (int, float)) and devendo_val > 0:
            status_pag = 'pendente'
            
        existing = Venda.query.filter_by(
            data=dt,
            cliente_id=cliente.id,
            vendedor_id=vendedor.id if vendedor else None,
            quantidade_sacos=qtd,
            preco_unitario=preco_unit,
            valor_liquido=valor_liquido
        ).first()
        if existing:
            continue
            
        venda = Venda(
            data=dt,
            cliente_id=cliente.id,
            vendedor_id=vendedor.id if vendedor else None,
            quantidade_sacos=qtd,
            preco_unitario=preco_unit,
            desconto=desconto,
            frete=0.0,
            tipo_frete=tipo_frete,
            forma_pagamento=str(forma_pag).strip().upper(),
            prazo_dias=prazo,
            valor_bruto=round(qtd * preco_unit, 2),
            valor_liquido=valor_liquido,
            custo_total=custo_total,
            lucro=lucro,
            margem=margem,
            comissao=comissao,
            status_pagamento=status_pag,
            valor_pago=valor_liquido if status_pag == 'pago' else 0.0,
            observacoes=str(obs)[:200] if obs else None
        )
        db.session.add(venda)
        db.session.flush()
        
        gerar_conta_receber(
            venda_id=venda.id,
            cliente_id=cliente.id,
            valor=valor_liquido,
            prazo_dias=prazo,
            descricao=f'Venda {qtd} sacos - Planilha',
            data_base=dt
        )
        
        if status_pag == 'pago':
            lancar_receita(
                valor=valor_liquido,
                descricao=f'Faturamento Venda #{venda.id} - Planilha',
                categoria='venda',
                referencia_id=venda.id,
                referencia_tipo='venda',
                data_lancamento=dt
            )
            
        imported += 1
        summary['vendas'] += 1
        
    return imported


def parse_purchases_sheet_custom(rows, summary, warnings):
    months_columns = [
        ('ABRIL', 0),
        ('MAIO', 4),
        ('JUNHO', 8),
        ('JULHO', 12),
        ('AGOSTO', 16),
        ('SETEMBRO', 20),
        ('OUTUBRO', 24),
        ('NOVEMBRO', 28),
        ('DEZEMBRO', 32)
    ]
    
    standard_prices = {
        'celulosico': 693.0,
        'celugel': 214.1,
        'fibra': 300.6,
        'embalagem': 8.1,
        'adesivo': 1.5
    }
    
    def get_supplier_name(desc):
        d = desc.upper()
        if 'MC QUIMICA' in d or 'MC Q' in d:
            return 'MC QUIMICA'
        if 'JUQUIA' in d:
            return 'VALE DO JUQUIA'
        if 'VIPEL' in d:
            return 'VIPEL'
        if 'FERMAFLEX' in d:
            return 'FERMAFLEX'
        if 'FLUKOCEL' in d:
            return 'FLUKOCEL'
        if 'TRANS' in d or 'MEDEIROS' in d:
            return 'TRANS MEDEIROS'
        return desc.strip().upper()
        
    def get_materia_prima_from_supplier(supplier_name, desc):
        d = desc.upper()
        tipo = 'celulosico'
        if 'CELUGEL' in d or 'MC QUIMICA 2' in d or (supplier_name == 'VALE DO JUQUIA' and 'CELUGEL' in d):
            tipo = 'celugel'
        elif supplier_name == 'VALE DO JUQUIA' or 'FIBRA' in d:
            tipo = 'fibra'
        elif supplier_name == 'VIPEL' or 'EMBALAGEM' in d:
            tipo = 'embalagem'
        elif supplier_name == 'FERMAFLEX' or 'ADESIVO' in d:
            tipo = 'adesivo'
            
        materia = MateriaPrima.query.filter_by(tipo=tipo).first()
        return materia, tipo

    imported = 0
    for month_name, col_idx in months_columns:
        for r_idx in range(1, len(rows)):
            row = rows[r_idx]
            if len(row) <= col_idx + 2:
                continue
                
            dt_val = row[col_idx]
            desc_val = row[col_idx + 1]
            valor_val = row[col_idx + 2]
            
            if not desc_val or str(desc_val).strip().upper() in ('TOTAL', 'A2', ''):
                continue
                
            dt = parse_date(dt_val)
            if not dt:
                continue
                
            valor = parse_number(valor_val)
            if valor <= 0:
                continue
                
            desc_clean = str(desc_val).strip()
            supplier_name = get_supplier_name(desc_clean)
            
            if 'FRETE' in desc_clean.upper():
                fornecedor = get_or_create_fornecedor(supplier_name)
                existing_desp = Financeiro.query.filter_by(
                    data=dt,
                    tipo='despesa',
                    categoria='frete',
                    valor=valor,
                    descricao=f'Despesa Frete - {desc_clean}'
                ).first()
                if not existing_desp:
                    lancar_despesa(
                        valor=valor,
                        descricao=f'Despesa Frete - {desc_clean}',
                        categoria='frete',
                        data_lancamento=dt
                    )
                    gerar_conta_pagar(
                        compra_id=None,
                        fornecedor_id=fornecedor.id if fornecedor else None,
                        valor=valor,
                        prazo_dias=0,
                        descricao=f'Frete - {desc_clean}',
                        categoria='frete',
                        data_base=dt
                    )
                    imported += 1
                    summary['compras'] += 1
                continue
                
            fornecedor = get_or_create_fornecedor(supplier_name)
            if not fornecedor:
                continue
                
            materia, tipo = get_materia_prima_from_supplier(supplier_name, desc_clean)
            if not materia:
                continue
                
            price = materia.preco_saco if (materia and materia.preco_saco > 0) else standard_prices.get(tipo, 10.0)
            quantidade = round(valor / price, 2)
            
            existing = Compra.query.filter_by(
                data=dt,
                fornecedor_id=fornecedor.id,
                materia_prima_id=materia.id,
                total_com_frete=valor
            ).first()
            if existing:
                continue
                
            compra = Compra(
                data=dt,
                fornecedor_id=fornecedor.id,
                materia_prima_id=materia.id,
                quantidade_sacos=quantidade,
                preco_unitario=price,
                frete_total=0.0,
                frete_por_saco=0.0,
                total=valor,
                total_com_frete=valor,
                numero_nf=None,
                prazo_pagamento=0,
                data_vencimento=dt,
                observacoes=f'Importado da planilha A2: {desc_clean}',
                criado_por=None
            )
            db.session.add(compra)
            db.session.flush()
            
            atualizar_custo_medio(materia, quantidade, price)
            materia.preco_saco = price
            
            entrada_mp(materia.id, quantidade, motivo='compra', referencia_id=compra.id,
                       referencia_tipo='compra', usuario_id=None)
                       
            gerar_conta_pagar(
                compra_id=compra.id,
                fornecedor_id=fornecedor.id,
                valor=valor,
                prazo_dias=0,
                descricao=f'Compra planilha - {materia.nome}',
                categoria='materia_prima',
                data_base=dt
            )
            
            lancar_despesa(
                valor=valor,
                descricao=f'Compra #{compra.id} - {materia.nome}',
                categoria='materia_prima',
                referencia_id=compra.id,
                referencia_tipo='compra',
                data_lancamento=dt
            )
            
            imported += 1
            summary['compras'] += 1
            
    recalcular_custo_produto()
    return imported


def import_excel_planilha(file_storage_or_path):
    if not file_storage_or_path:
        raise ValueError('Nenhum arquivo selecionado.')

    if hasattr(file_storage_or_path, 'filename'):
        filename = secure_filename(file_storage_or_path.filename)
        if not allowed_file(filename):
            raise ValueError('Somente arquivos .xls ou .xlsx são aceitos.')
        file_storage_or_path.stream.seek(0)
        content = file_storage_or_path.read()
        if not content:
            raise ValueError('O arquivo está vazio.')
        excel = pd.ExcelFile(io.BytesIO(content))
    elif isinstance(file_storage_or_path, (str, os.PathLike)):
        path = os.fspath(file_storage_or_path)
        filename = secure_filename(os.path.basename(path))
        if not allowed_file(filename):
            raise ValueError('Somente arquivos .xls ou .xlsx são aceitos.')
        if not os.path.exists(path) or os.path.getsize(path) <= 0:
            raise ValueError('O arquivo está vazio.')
        with open(path, 'rb') as handle:
            content = handle.read()
        excel = pd.ExcelFile(io.BytesIO(content))
    else:
        raise ValueError('Formato de arquivo inválido.')
    summary = {
        'vendas': 0,
        'compras': 0,
        'clientes': 0,
        'fornecedores': 0,
        'materias_primas': 0,
        'planilhas_lidas': 0,
        'warnings': []
    }

    # First round: register all Clients & Sellers across all sales sheets to avoid FK issues
    vendedores_set = set()
    clientes_set = set()
    for sheet_name in excel.sheet_names:
        if not sheet_name.startswith('Vendas -'):
            continue
        try:
            df = excel.parse(sheet_name, header=None, dtype=object)
            rows = [list(r) for r in df.values.tolist()]
            for r_idx in range(3, len(rows)):
                row = rows[r_idx]
                if not row or all(c is None for c in row[:5]):
                    continue
                v_nome = row[1]
                c_nome = row[2]
                if v_nome and str(v_nome).strip():
                    vendedores_set.add(str(v_nome).strip().upper())
                if c_nome and str(c_nome).strip():
                    clientes_set.add(str(c_nome).strip().upper())
        except Exception:
            pass

    for v_nome in vendedores_set:
        get_or_create_vendedor(v_nome)
    for c_nome in clientes_set:
        get_or_create_cliente(c_nome)
    db.session.commit()

    # Second round: do actual parsing
    for sheet_name in excel.sheet_names:
        try:
            df = excel.parse(sheet_name, header=None, dtype=object)
        except Exception:
            summary['warnings'].append(f'Não foi possível ler a aba {sheet_name}.')
            continue

        rows = [list(r) for r in df.values.tolist()]
        summary['planilhas_lidas'] += 1

        if sheet_name.startswith('Vendas -'):
            parse_sales_sheet_custom(sheet_name, rows, summary, summary['warnings'])
        elif sheet_name.upper() == 'A2':
            parse_purchases_sheet_custom(rows, summary, summary['warnings'])
        else:
            # Fallback parsing
            lower_rows = [[normalize_text(cell).lower() if normalize_text(cell) else '' for cell in row] for row in rows]
            if is_sales_sheet(sheet_name, lower_rows[0] if lower_rows else []):
                # Generic parsing if custom conditions didn't trigger
                # We reuse the custom one if they match
                parse_sales_sheet_custom(sheet_name, rows, summary, summary['warnings'])
            elif is_purchase_sheet(sheet_name, lower_rows[0] if lower_rows else []):
                summary['warnings'].append(
                    f'Aba de compras reconhecida ({sheet_name}), mas o formato não corresponde ao parser esperado. ' 
                    'Use a aba nomeada como "A2" ou um formato compatível.'
                )

    db.session.commit()
    return summary
