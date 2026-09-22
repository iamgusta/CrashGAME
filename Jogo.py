import pygame
import sys
import os
import math
import random
from collections import deque

pygame.init()

LARGURA = 1366
ALTURA = 768
FPS = 60

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Crash do Gustavo")
clock = pygame.time.Clock()


# CORES

CEU = (65, 190, 240)
BRANCO = (255, 255, 255)
PRETO = (20, 20, 25)

VERDE = (70, 200, 75)
VERDE_ESCURO = (35, 125, 50)

TERRA = (155, 95, 50)
TERRA_ESCURO = (110, 65, 35)

TIJOLO = (225, 135, 65)
TIJOLO_ESCURO = (175, 90, 40)

AMARELO = (255, 220, 45)
DOURADO = (245, 175, 20)

VERMELHO = (220, 45, 55)
ROXO = (125, 70, 180)


# FONTES


fonte_pequena = pygame.font.SysFont("arial", 18, bold=True)
fonte_hud = pygame.font.SysFont("arial", 24, bold=True)
fonte_media = pygame.font.SysFont("arial", 42, bold=True)
fonte_grande = pygame.font.SysFont("arial", 72, bold=True)


# PASTA DAS IMAGENS


PASTA_JOGO = os.path.dirname(os.path.abspath(__file__))
PASTA_IMAGENS = os.path.join(PASTA_JOGO, "imagens")


# FUNÇÕES GERAIS

def texto(mensagem, fonte, cor, posicao, centro=False):
    imagem = fonte.render(mensagem, True, cor)
    rect = imagem.get_rect()

    if centro:
        rect.center = posicao
    else:
        rect.topleft = posicao

    tela.blit(imagem, rect)


def distancia_cor(a, b):
    return math.sqrt(
        (a[0] - b[0]) ** 2 +
        (a[1] - b[1]) ** 2 +
        (a[2] - b[2]) ** 2
    )


# REMOÇÃO INTELIGENTE DO FUNDO DO JPG

def remover_fundo_jpg(imagem, tolerancia=85):
    """Remove automaticamente o fundo xadrez/branco das imagens do Crash.

    A remoção é feita somente em áreas conectadas às bordas da imagem.
    Assim, o branco dos olhos, dentes e tênis continua visível.
    """
    imagem = imagem.convert_alpha()
    largura = imagem.get_width()
    altura = imagem.get_height()

    # Pega várias cores das bordas para descobrir o fundo real da imagem.
    pontos_borda = []
    for x in range(largura):
        pontos_borda.append((x, 0))
        pontos_borda.append((x, altura - 1))
    for y in range(altura):
        pontos_borda.append((0, y))
        pontos_borda.append((largura - 1, y))

    cores_borda = [imagem.get_at(p)[:3] for p in pontos_borda]

    # Cores de referência dos cantos.
    cores_referencia = [
        imagem.get_at((0, 0))[:3],
        imagem.get_at((largura - 1, 0))[:3],
        imagem.get_at((0, altura - 1))[:3],
        imagem.get_at((largura - 1, altura - 1))[:3],
    ]

    visitados = set()
    fila = deque()

    def eh_fundo(cor):
        r, g, b = cor

        # Fundo xadrez normalmente é branco/cinza claro e pouco saturado.
        maximo = max(r, g, b)
        minimo = min(r, g, b)
        saturacao = maximo - minimo
        neutro_claro = maximo >= 170 and saturacao <= 45

        # Também aceita cores próximas às cores encontradas nas bordas.
        perto_da_borda = any(
            distancia_cor(cor, referencia) <= tolerancia
            for referencia in cores_referencia
        )

        return neutro_claro or perto_da_borda

    # Começa somente pelas áreas que tocam a borda.
    for ponto in pontos_borda:
        if ponto in visitados:
            continue
        if eh_fundo(imagem.get_at(ponto)[:3]):
            visitados.add(ponto)
            fila.append(ponto)

    # Flood fill: remove todo o fundo conectado à borda.
    while fila:
        x, y = fila.popleft()
        imagem.set_at((x, y), (0, 0, 0, 0))

        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nx < 0 or nx >= largura or ny < 0 or ny >= altura:
                continue
            if (nx, ny) in visitados:
                continue

            if eh_fundo(imagem.get_at((nx, ny))[:3]):
                visitados.add((nx, ny))
                fila.append((nx, ny))

    # Limpa um pequeno halo cinza/branco que pode ficar nas bordas do Crash.
    # Só altera pixels próximos de uma área já transparente, sem apagar o branco
    # interno do personagem.
    for y in range(altura):
        for x in range(largura):
            cor = imagem.get_at((x, y))
            if cor.a == 0:
                continue

            r, g, b = cor.r, cor.g, cor.b
            maximo = max(r, g, b)
            minimo = min(r, g, b)

            if maximo >= 190 and (maximo - minimo) <= 38:
                vizinho_transparente = False
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < largura and 0 <= ny < altura:
                        if imagem.get_at((nx, ny)).a == 0:
                            vizinho_transparente = True
                            break
                if vizinho_transparente:
                    imagem.set_at((x, y), (r, g, b, 0))

    return imagem


# CARREGAR CRASH

def carregar_crash():
    """Carrega os sprites Crash1/Crash2 de forma tolerante a extensões."""
    frames = []

    # Aceita JPG/JPEG/PNG e também nomes com maiúsculas/minúsculas.
    nomes_base = ["Crash1", "Crash2"]
    extensoes = [".jpg", ".jpeg", ".png", ".webp"]

    for nome_base in nomes_base:
        caminho_encontrado = None

        # Primeiro tenta os nomes mais comuns.
        for extensao in extensoes:
            candidato = os.path.join(PASTA_IMAGENS, nome_base + extensao)
            if os.path.isfile(candidato):
                caminho_encontrado = candidato
                break

        # Se o Windows salvou com outra capitalização, procura pela base.
        if caminho_encontrado is None and os.path.isdir(PASTA_IMAGENS):
            base_minuscula = nome_base.lower()
            for arquivo in os.listdir(PASTA_IMAGENS):
                caminho = os.path.join(PASTA_IMAGENS, arquivo)
                if (
                    os.path.isfile(caminho)
                    and os.path.splitext(arquivo)[0].lower() == base_minuscula
                    and os.path.splitext(arquivo)[1].lower() in extensoes
                ):
                    caminho_encontrado = caminho
                    break

        if caminho_encontrado is None:
            print(f"Imagem não encontrada: {nome_base} (.jpg/.jpeg/.png/.webp)")
            continue

        print("Procurando:", caminho_encontrado)

        try:
            imagem = pygame.image.load(caminho_encontrado).convert()

            # Remove o fundo das imagens.
            imagem = remover_fundo_jpg(imagem, 60)

            # Mantém a proporção e padroniza a altura dos sprites.
            altura_sprite = 112
            largura_sprite = max(
                1,
                int(
                    imagem.get_width() *
                    altura_sprite /
                    imagem.get_height()
                )
            )

            imagem = pygame.transform.smoothscale(
                imagem,
                (largura_sprite, altura_sprite)
            )

            frames.append(imagem)
            print("Sprite Crash carregado:", os.path.basename(caminho_encontrado))

        except (pygame.error, ValueError) as erro:
            print("Erro ao carregar", caminho_encontrado, ":", erro)

    if not frames:
        print()
        print("ERRO: Nenhum sprite do Crash foi encontrado.")
        print("Coloque na pasta 'imagens' pelo menos:")
        print("  Crash1.jpg")
        print("  Crash2.jpg")
        print()

    return frames


CRASH_FRAMES = carregar_crash()


# PARTÍCULAS

particulas = []


def criar_particulas(x, y, quantidade, cor):

    for _ in range(quantidade):

        particulas.append({
            "x": float(x),
            "y": float(y),
            "vx": random.uniform(-3, 3),
            "vy": random.uniform(-4, -1),
            "vida": random.randint(15, 30),
            "cor": cor,
        })


def atualizar_particulas():

    for particula in particulas[:]:

        particula["x"] += particula["vx"]
        particula["y"] += particula["vy"]

        particula["vy"] += 0.18

        particula["vida"] -= 1

        if particula["vida"] <= 0:

            particulas.remove(
                particula
            )


def desenhar_particulas():

    for particula in particulas:

        pygame.draw.circle(
            tela,
            particula["cor"],
            (
                int(
                    particula["x"] -
                    camera_x
                ),
                int(
                    particula["y"]
                ),
            ),
            3,
        )


# FUNDO

def desenhar_nuvem(x, y, escala):

    pygame.draw.circle(
        tela,
        BRANCO,
        (
            int(x),
            int(y)
        ),
        int(25 * escala),
    )

    pygame.draw.circle(
        tela,
        BRANCO,
        (
            int(
                x +
                35 * escala
            ),
            int(
                y -
                10 * escala
            ),
        ),
        int(35 * escala),
    )

    pygame.draw.circle(
        tela,
        BRANCO,
        (
            int(
                x +
                65 * escala
            ),
            int(y),
        ),
        int(25 * escala),
    )


def desenhar_fundo():
    # Céu em degradê para ficar mais vivo e próximo de um cenário de plataforma 2D.
    topo = (72, 190, 235)
    horizonte = (150, 220, 245)
    for y in range(ALTURA):
        t = min(1.0, y / 600.0)
        cor = tuple(int(topo[i] * (1 - t) + horizonte[i] * t) for i in range(3))
        pygame.draw.line(tela, cor, (0, y), (LARGURA, y))

    # Brilho suave atrás do sol.
    pygame.draw.circle(tela, (255, 235, 125), (1030, 100), 78)
    pygame.draw.circle(tela, (255, 220, 55), (1030, 100), 55)

    # Montanhas distantes.
    deslocamento = int(camera_x * 0.12) % 1350
    for base in range(-1350, LARGURA + 1400, 450):
        x = base - deslocamento
        pygame.draw.polygon(
            tela,
            (105, 175, 125),
            [(x, 505), (x + 225, 285), (x + 450, 505)],
        )

    # Montanhas principais com dois tons de verde.
    deslocamento = int(camera_x * 0.18) % 900
    for base in range(-900, LARGURA + 1000, 450):
        x = base - deslocamento

        pygame.draw.polygon(
            tela,
            (65, 150, 90),
            [(x, 505), (x + 225, 250), (x + 450, 505)],
        )

        pygame.draw.polygon(
            tela,
            (105, 190, 115),
            [(x + 80, 505), (x + 225, 320), (x + 370, 505)],
        )

    # Faixa de vegetação no horizonte.
    pygame.draw.rect(tela, (72, 160, 88), (0, 500, LARGURA, 105))
    pygame.draw.rect(tela, (88, 178, 95), (0, 500, LARGURA, 12))

    # Nuvens.
    nuvens = [
        (100, 120, 1.0),
        (500, 170, 0.8),
        (850, 125, 0.9),
        (1250, 210, 0.75),
    ]

    for x, y, escala in nuvens:
        desenhar_nuvem(x - camera_x * 0.3, y, escala)



# PLATAFORMA


class Plataforma:

    def __init__(
        self,
        x,
        y,
        largura,
        altura
    ):

        # Área usada para desenhar.
        self.rect = pygame.Rect(
            x,
            y,
            largura,
            altura,
        )

        # CORREÇÃO IMPORTANTE
        
        self.colisao = pygame.Rect(
            x,
            y,
            largura,
            20,
        )

    def desenhar(self):

        r = self.rect.move(
            -int(camera_x),
            0,
        )

        if (
            r.right < 0
            or r.left > LARGURA
        ):
            return

        # Terra
        pygame.draw.rect(
            tela,
            TERRA,
            r,
        )

        # Textura
        for x in range(
            r.left + 15,
            r.right,
            50
        ):

            pygame.draw.circle(
                tela,
                TERRA_ESCURO,
                (
                    x,
                    r.top + 42
                ),
                3,
            )

        # Grama em camadas, com uma borda mais forte.
        pygame.draw.rect(
            tela, VERDE_ESCURO,
            (r.left, r.top, r.width, 22),
        )
        pygame.draw.rect(
            tela, VERDE,
            (r.left, r.top, r.width, 16),
        )
        pygame.draw.rect(
            tela, (92, 215, 95),
            (r.left, r.top, r.width, 6),
        )

        # Pequenas folhas/grama para tirar o aspecto chapado.
        for x in range(r.left + 10, r.right, 28):
            pygame.draw.line(
                tela, (55, 145, 65),
                (x, r.top + 15),
                (x + 4, r.top + 5),
                2,
            )
            pygame.draw.line(
                tela, (105, 225, 105),
                (x + 4, r.top + 10),
                (x + 10, r.top + 4),
                2,
            )



# BLOCO


class Bloco:

    def __init__(
        self,
        x,
        y,
        tipo="normal"
    ):

        self.rect = pygame.Rect(
            x,
            y,
            52,
            52,
        )

        self.tipo = tipo
        self.usado = False

    def bater(self):

        if (
            self.tipo == "?"
            and not self.usado
        ):

            self.usado = True

            moedas.append(
                Moeda(
                    self.rect.centerx,
                    self.rect.top - 35,
                )
            )

            criar_particulas(
                self.rect.centerx,
                self.rect.top,
                10,
                AMARELO,
            )

    def desenhar(self):

        r = self.rect.move(
            -int(camera_x),
            0,
        )

        if (
            r.right < 0
            or r.left > LARGURA
        ):
            return

        # Bloco ?
        if (
            self.tipo == "?"
            and not self.usado
        ):

            pygame.draw.rect(
                tela,
                AMARELO,
                r,
                border_radius=7,
            )

            pygame.draw.rect(
                tela,
                (180, 125, 15),
                r,
                4,
                border_radius=7,
            )

            texto(
                "?",
                fonte_media,
                BRANCO,
                r.center,
                centro=True,
            )

        else:

            pygame.draw.rect(
                tela,
                TIJOLO,
                r,
                border_radius=5,
            )

            pygame.draw.rect(
                tela,
                TIJOLO_ESCURO,
                r,
                3,
                border_radius=5,
            )

            pygame.draw.line(
                tela,
                TIJOLO_ESCURO,
                (
                    r.left,
                    r.centery
                ),
                (
                    r.right,
                    r.centery
                ),
                3,
            )

            pygame.draw.line(
                tela,
                TIJOLO_ESCURO,
                (
                    r.centerx,
                    r.top
                ),
                (
                    r.centerx,
                    r.centery
                ),
                3,
            )

            pygame.draw.line(
                tela,
                TIJOLO_ESCURO,
                (
                    r.left + 15,
                    r.centery
                ),
                (
                    r.left + 15,
                    r.bottom
                ),
                3,
            )



# MOEDA


class Moeda:

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.tempo = (
            random.random() * 6
        )

        self.coletada = False

    @property
    def rect(self):

        return pygame.Rect(
            self.x - 13,
            self.y - 18,
            26,
            36,
        )

    def atualizar(self):

        self.tempo += 0.12

    def desenhar(self):

        if self.coletada:
            return

        x = int(
            self.x - camera_x
        )

        y = int(
            self.y +
            math.sin(
                self.tempo
            ) * 5
        )

        largura = max(
            5,
            int(
                15 *
                abs(
                    math.cos(
                        self.tempo
                    )
                )
            ),
        )

        pygame.draw.ellipse(
            tela,
            DOURADO,
            (
                x - largura,
                y - 18,
                largura * 2,
                36,
            ),
        )

        pygame.draw.ellipse(
            tela,
            AMARELO,
            (
                x - largura // 2,
                y - 13,
                max(
                    1,
                    largura
                ),
                26,
            ),
        )



# INIMIGO


class Inimigo:

    def __init__(
        self,
        x,
        y,
        esquerda,
        direita
    ):

        self.x = float(x)
        self.y = float(y)

        self.esquerda = esquerda
        self.direita = direita

        self.velocidade = 1.5
        self.direcao = 1

        self.vivo = True
        self.animacao = 0

    @property
    def rect(self):

        return pygame.Rect(
            int(self.x - 25),
            int(self.y - 40),
            50,
            40,
        )

    def atualizar(self):

        if not self.vivo:
            return

        self.x += (
            self.velocidade *
            self.direcao
        )

        if self.x <= self.esquerda:

            self.x = self.esquerda
            self.direcao = 1

        if self.x >= self.direita:

            self.x = self.direita
            self.direcao = -1

        self.animacao += 1

    def desenhar(self):

        if not self.vivo:
            return

        x = int(
            self.x - camera_x
        )

        y = int(self.y)

        # Sombra
        pygame.draw.ellipse(
            tela,
            (70, 80, 90),
            (
                x - 25,
                y - 7,
                50,
                10,
            ),
        )

        # Corpo
        pygame.draw.ellipse(
            tela,
            ROXO,
            (
                x - 24,
                y - 38,
                48,
                38,
            ),
        )

        # Olhos
        pygame.draw.circle(
            tela,
            BRANCO,
            (
                x - 9,
                y - 25
            ),
            8,
        )

        pygame.draw.circle(
            tela,
            BRANCO,
            (
                x + 9,
                y - 25
            ),
            8,
        )

        pygame.draw.circle(
            tela,
            PRETO,
            (
                x - 9,
                y - 25
            ),
            3,
        )

        pygame.draw.circle(
            tela,
            PRETO,
            (
                x + 9,
                y - 25
            ),
            3,
        )

        # Pés animados
        movimento = int(
            math.sin(
                self.animacao / 7
            ) * 4
        )

        pygame.draw.ellipse(
            tela,
            (70, 45, 100),
            (
                x - 26 - movimento,
                y - 7,
                25,
                10,
            ),
        )

        pygame.draw.ellipse(
            tela,
            (70, 45, 100),
            (
                x + 1 + movimento,
                y - 7,
                25,
                10,
            ),
        )


# CANO

class Cano:

    def __init__(
        self,
        x,
        y,
        altura
    ):

        self.x = x
        self.y = y
        self.altura = altura

        self.rect = pygame.Rect(
            x,
            y - altura,
            75,
            altura,
        )

    def desenhar(self):

        r = self.rect.move(
            -int(camera_x),
            0,
        )

        # Corpo
        pygame.draw.rect(
            tela,
            VERDE_ESCURO,
            r,
        )

        pygame.draw.rect(
            tela,
            VERDE,
            (
                r.left + 8,
                r.top,
                r.width - 16,
                r.height,
            ),
        )

        # Topo
        topo = pygame.Rect(
            r.left - 8,
            r.top - 17,
            r.width + 16,
            24,
        )

        pygame.draw.rect(
            tela,
            VERDE_ESCURO,
            topo,
            border_radius=8,
        )

        pygame.draw.rect(
            tela,
            VERDE,
            (
                topo.left + 7,
                topo.top + 4,
                topo.width - 14,
                topo.height - 8,
            ),
            border_radius=6,
        )


# PLAYER

class Player:

    def __init__(self):

        self.x = 150.0
        self.y = 600.0

   
        self.largura = 46

        self.altura_normal = 104
        self.altura_abaixado = 62

        self.vel_x = 0.0
        self.vel_y = 0.0

        # Movimento mais responsivo.
        self.velocidade_max = 7.0
        self.velocidade_frente = 2.8
        self.aceleracao = 1.8
        self.frenagem = 1.35

        self.pulo = -16
        self.gravidade = 0.75
        self.coyote_timer = 0
        self.jump_buffer = 0

        self.no_chao = False
        self.abaixado = False

        self.vidas = 3
        self.invencivel = 0
        self.morto = False

        self.frame = 0
        self.timer_frame = 0

        self.direcao = 1

    @property
    def altura_atual(self):

        if self.abaixado:
            return self.altura_abaixado

        return self.altura_normal

    @property
    def rect(self):

        return pygame.Rect(
            int(
                self.x -
                self.largura / 2
            ),
            int(
                self.y -
                self.altura_atual
            ),
            self.largura,
            self.altura_atual,
        )

    def pular(self):

        if self.morto:
            return

        # Buffer de pulo: se o jogador apertar ESPAÇO um pouco antes
        # de tocar o chão, o pulo acontece assim que aterrissar.
        if self.no_chao or self.coyote_timer > 0:
            self._executar_pulo()
        else:
            self.jump_buffer = 8

    def _executar_pulo(self):

        self.abaixado = False
        self.vel_y = self.pulo
        self.no_chao = False
        self.coyote_timer = 0
        self.jump_buffer = 0

        criar_particulas(
            self.x,
            self.y,
            8,
            BRANCO,
        )

    def dano(self):

        if (
            self.invencivel > 0
            or self.morto
        ):
            return

        self.vidas -= 1

        self.invencivel = 100

        self.vel_y = -10
        self.vel_x = -6

        criar_particulas(
            self.x,
            self.y - 35,
            15,
            VERMELHO,
        )

        if self.vidas <= 0:
            self.morto = True

    def atualizar(self):

        if self.morto:
            return

        teclas = pygame.key.get_pressed()

        # ====================================================
        # ABAIXAR
        # ====================================================

        self.abaixado = (
            (
                teclas[pygame.K_DOWN]
                or teclas[pygame.K_s]
            )
            and self.no_chao
        )

        # ====================================================
        # MOVIMENTO RESPONSIVO
        # ====================================================
        # Sem tecla: o jogo continua andando para frente.
        # Esquerda/direita passam a responder imediatamente, mas
        # usam aceleração para não dar aquela sensação de atraso.
        esquerda = teclas[pygame.K_LEFT] or teclas[pygame.K_a]
        direita = teclas[pygame.K_RIGHT] or teclas[pygame.K_d]

        if esquerda and not direita:
            alvo_x = -self.velocidade_max
            self.direcao = -1
        elif direita and not esquerda:
            alvo_x = self.velocidade_max
            self.direcao = 1
        elif esquerda and direita:
            alvo_x = 0.0
        else:
            alvo_x = self.velocidade_frente
            self.direcao = 1

        diferenca = alvo_x - self.vel_x

        if diferenca > 0:
            self.vel_x = min(
                self.vel_x + self.aceleracao,
                alvo_x
            )
        elif diferenca < 0:
            self.vel_x = max(
                self.vel_x - self.aceleracao,
                alvo_x
            )

        # Frenagem extra quando solta uma direção manual.
        if not esquerda and not direita:
            if self.vel_x > self.velocidade_frente:
                self.vel_x = max(
                    self.velocidade_frente,
                    self.vel_x - self.frenagem
                )
            elif self.vel_x < self.velocidade_frente:
                self.vel_x = min(
                    self.velocidade_frente,
                    self.vel_x + self.frenagem
                )

        self.x += self.vel_x

        if self.x < 30:
            self.x = 30
            self.vel_x = max(0.0, self.vel_x)

        # ====================================================
        # COLISÃO HORIZONTAL COM PLATAFORMAS
        # ====================================================

        r = self.rect

        for plataforma in plataformas:

            if r.colliderect(
                plataforma.colisao
            ):

                if self.vel_x > 0:

                    self.x = (
                        plataforma.colisao.left
                        -
                        self.largura / 2
                    )

                elif self.vel_x < 0:

                    self.x = (
                        plataforma.colisao.right
                        +
                        self.largura / 2
                    )

                r = self.rect

        # ====================================================
        # COLISÃO HORIZONTAL COM BLOCOS
        # ====================================================

        for bloco in blocos:

            if r.colliderect(
                bloco.rect
            ):

                if self.vel_x > 0:

                    self.x = (
                        bloco.rect.left
                        -
                        self.largura / 2
                    )

                elif self.vel_x < 0:

                    self.x = (
                        bloco.rect.right
                        +
                        self.largura / 2
                    )

                r = self.rect

        # ====================================================
        # COLISÃO HORIZONTAL COM CANOS
        # ====================================================

        for cano in canos:

            if r.colliderect(
                cano.rect
            ):

                if self.vel_x > 0:

                    self.x = (
                        cano.rect.left
                        -
                        self.largura / 2
                    )

                elif self.vel_x < 0:

                    self.x = (
                        cano.rect.right
                        +
                        self.largura / 2
                    )

                r = self.rect

        # ====================================================
        # GRAVIDADE
        # ====================================================

        self.vel_y += self.gravidade

        if self.vel_y > 18:
            self.vel_y = 18

        self.y += self.vel_y

        self.no_chao = False

        r = self.rect

        # ====================================================
        # COLISÃO VERTICAL COM PLATAFORMAS
        # ====================================================

        for plataforma in plataformas:

            if r.colliderect(
                plataforma.colisao
            ):

                if self.vel_y > 0:

                    self.y = (
                        plataforma.colisao.top
                    )

                    self.vel_y = 0

                    self.no_chao = True

                elif self.vel_y < 0:

                    self.y = (
                        plataforma.colisao.bottom
                        +
                        self.altura_atual
                    )

                    self.vel_y = 0

                r = self.rect

        # ====================================================
        # COLISÃO VERTICAL COM BLOCOS
        # ====================================================

        for bloco in blocos:

            if r.colliderect(
                bloco.rect
            ):

                if self.vel_y < 0:

                    self.y = (
                        bloco.rect.bottom
                        +
                        self.altura_atual
                    )

                    self.vel_y = 0

                    bloco.bater()

                elif self.vel_y > 0:

                    self.y = (
                        bloco.rect.top
                    )

                    self.vel_y = 0

                    self.no_chao = True

                r = self.rect

        # ====================================================
        # COLISÃO VERTICAL COM CANOS
        # ====================================================

        for cano in canos:

            if r.colliderect(
                cano.rect
            ):

                if self.vel_y > 0:

                    self.y = (
                        cano.rect.top
                    )

                    self.vel_y = 0

                    self.no_chao = True

                elif self.vel_y < 0:

                    self.y = (
                        cano.rect.bottom
                        +
                        self.altura_atual
                    )

                    self.vel_y = 0

                r = self.rect

        # ====================================================
        # RESPONSIVIDADE DO PULO
        # ====================================================
        if self.no_chao:
            self.coyote_timer = 6
        elif self.coyote_timer > 0:
            self.coyote_timer -= 1

        if self.jump_buffer > 0:
            self.jump_buffer -= 1
            if self.no_chao:
                self._executar_pulo()

        # ====================================================
        # ANIMAÇÃO
        # ====================================================

        if (
            abs(self.vel_x) > 0
            and self.no_chao
        ):

            self.timer_frame += 1

            if self.timer_frame >= 5:

                self.timer_frame = 0

                self.frame += 1

        # ====================================================
        # INVENCIBILIDADE
        # ====================================================

        if self.invencivel > 0:

            self.invencivel -= 1

    def desenhar(self):

        if (
            self.invencivel > 0
            and
            (
                self.invencivel // 5
            ) % 2 == 0
        ):

            return

        x = int(
            self.x - camera_x
        )

        y = int(self.y)

        # ====================================================
        # CRASH REAL
        # ====================================================

        if CRASH_FRAMES:

            imagem_original = (
                CRASH_FRAMES[
                    self.frame %
                    len(CRASH_FRAMES)
                ]
            )

            imagem = imagem_original

            if self.direcao == -1:

                imagem = (
                    pygame.transform.flip(
                        imagem,
                        True,
                        False,
                    )
                )

            # =================================================
            # NORMAL / ABAIXADO
            # =================================================

            if self.abaixado:

                # Abaixado: reduz a altura, mas continua mantendo
                # a mesma proporção da imagem original.
                altura_abaixado = 72
                largura_abaixado = max(
                    1,
                    int(
                        imagem.get_width() *
                        altura_abaixado /
                        imagem.get_height()
                    )
                )

                imagem = pygame.transform.smoothscale(
                    imagem,
                    (
                        largura_abaixado,
                        altura_abaixado
                    )
                )

                pos_y = y - altura_abaixado

            else:

                # Não força 65x82: isso deformava o Luffy.
                # As quatro fotos continuam sendo as mesmas.
                pos_y = y - imagem.get_height()

            tela.blit(
                imagem,
                (
                    x -
                    imagem.get_width() // 2,
                    pos_y,
                ),
            )

        # ====================================================
        # PERSONAGEM RESERVA
        # ====================================================

        else:

            if self.abaixado:

                pygame.draw.circle(
                    tela,
                    (245, 190, 145),
                    (
                        x,
                        y - 32
                    ),
                    16,
                )

                pygame.draw.ellipse(
                    tela,
                    VERMELHO,
                    (
                        x - 24,
                        y - 38,
                        48,
                        32,
                    ),
                )

                pygame.draw.ellipse(
                    tela,
                    AMARELO,
                    (
                        x - 25,
                        y - 50,
                        50,
                        15,
                    ),
                )

                # Cabelo preto
                pygame.draw.arc(
                    tela,
                    PRETO,
                    (
                        x - 16,
                        y - 45,
                        32,
                        25,
                    ),
                    math.pi,
                    math.pi * 2,
                    5,
                )

            else:

                pygame.draw.circle(
                    tela,
                    (245, 190, 145),
                    (
                        x,
                        y - 65
                    ),
                    20,
                )

                pygame.draw.ellipse(
                    tela,
                    VERMELHO,
                    (
                        x - 22,
                        y - 55,
                        44,
                        48,
                    ),
                )

                pygame.draw.ellipse(
                    tela,
                    AMARELO,
                    (
                        x - 27,
                        y - 85,
                        54,
                        18,
                    ),
                )

                # Cabelo preto
                pygame.draw.arc(
                    tela,
                    PRETO,
                    (
                        x - 20,
                        y - 87,
                        40,
                        35,
                    ),
                    math.pi,
                    math.pi * 2,
                    6,
                )


# ============================================================
# MUNDO
# ============================================================

plataformas = []
blocos = []
moedas = []
inimigos = []
canos = []

player = Player()

camera_x = 0

# Largura total da fase.
LARGURA_MUNDO = 6350

pontuacao = 0
moedas_coletadas = 0

jogo_iniciado = False
pausado = False
game_over = False
vitoria = False


# ============================================================
# CRIAR FASE
# ============================================================

def criar_fase():

    plataformas.clear()
    blocos.clear()
    moedas.clear()
    inimigos.clear()
    canos.clear()

    # ========================================================
    # CHÃO
    # ========================================================

    plataformas.extend([
        Plataforma(
            0,
            600,
            900,
            100
        ),

        Plataforma(
            1050,
            600,
            850,
            100
        ),

        Plataforma(
            2050,
            600,
            1000,
            100
        ),

        Plataforma(
            3150,
            600,
            1000,
            100
        ),

        Plataforma(
            4250,
            600,
            1200,
            100
        ),

        Plataforma(
            5550,
            600,
            800,
            100
        ),
    ])

    # ========================================================
    # PLATAFORMAS SUSPENSAS
    # ========================================================

    plataformas.extend([
        Plataforma(
            350,
            470,
            200,
            130
        ),

        Plataforma(
            680,
            400,
            190,
            200
        ),

        Plataforma(
            1150,
            470,
            220,
            130
        ),

        Plataforma(
            1500,
            390,
            220,
            210
        ),

        Plataforma(
            1780,
            470,
            170,
            130
        ),

        Plataforma(
            2200,
            460,
            210,
            140
        ),

        Plataforma(
            2550,
            380,
            220,
            220
        ),

        Plataforma(
            2900,
            470,
            170,
            130
        ),

        Plataforma(
            3300,
            440,
            220,
            160
        ),

        Plataforma(
            3650,
            350,
            230,
            250
        ),

        Plataforma(
            4000,
            470,
            180,
            130
        ),

        Plataforma(
            4450,
            430,
            220,
            170
        ),

        Plataforma(
            4800,
            350,
            230,
            250
        ),

        Plataforma(
            5200,
            450,
            200,
            150
        ),
    ])

    # ========================================================
    # BLOCOS ORGANIZADOS
    # ========================================================

    grupos_blocos = [

        (400, 390, 3),

        (850, 300, 2),

        (1200, 390, 3),

        (1540, 310, 2),

        (2250, 380, 3),

        (2600, 300, 3),

        (3340, 380, 2),

        (3700, 270, 3),

        (4480, 370, 3),

        (4840, 270, 3),
    ]

    for x, y, quantidade in grupos_blocos:

        for i in range(
            quantidade
        ):

            blocos.append(
                Bloco(
                    x + i * 52,
                    y
                )
            )

    # ========================================================
    # BLOCOS ?
    # ========================================================

    blocos_interrogacao = [

        (505, 390),

        (900, 300),

        (1280, 390),

        (1592, 310),

        (2350, 380),

        (2700, 300),

        (3400, 380),

        (3752, 270),

        (4580, 370),

        (4944, 270),
    ]

    for x, y in blocos_interrogacao:

        blocos.append(
            Bloco(
                x,
                y,
                "?"
            )
        )

    # ========================================================
    # MOEDAS
    # ========================================================

    moedas_posicoes = [

        (260, 520),
        (320, 470),
        (380, 420),
        (440, 470),
        (500, 520),

        (760, 340),
        (820, 290),
        (880, 340),

        (1120, 520),
        (1180, 470),
        (1240, 420),
        (1300, 470),
        (1360, 520),

        (1510, 330),
        (1570, 280),
        (1630, 330),

        (2180, 520),
        (2240, 470),
        (2300, 420),
        (2360, 470),
        (2420, 520),

        (2570, 320),
        (2630, 270),
        (2690, 220),
        (2750, 270),
        (2810, 320),

        (3270, 520),
        (3330, 470),
        (3390, 420),
        (3450, 470),
        (3510, 520),

        (3670, 290),
        (3730, 240),
        (3790, 190),
        (3850, 240),
        (3910, 290),

        (4420, 520),
        (4480, 470),
        (4540, 420),
        (4600, 470),
        (4660, 520),

        (4780, 300),
        (4840, 250),
        (4900, 200),
        (4960, 250),
        (5020, 300),
    ]

    for x, y in moedas_posicoes:

        moedas.append(
            Moeda(
                x,
                y
            )
        )

    # ========================================================
    # INIMIGOS
    # ========================================================

    inimigos.extend([

        Inimigo(
            720,
            600,
            600,
            850
        ),

        Inimigo(
            1300,
            470,
            1150,
            1350
        ),

        Inimigo(
            1700,
            600,
            1500,
            1850
        ),

        Inimigo(
            2300,
            460,
            2200,
            2400
        ),

        Inimigo(
            2800,
            600,
            2600,
            3000
        ),

        Inimigo(
            3400,
            440,
            3300,
            3500
        ),

        Inimigo(
            3900,
            600,
            3650,
            4050
        ),

        Inimigo(
            4550,
            430,
            4450,
            4650
        ),

        Inimigo(
            5050,
            600,
            4800,
            5200
        ),

        Inimigo(
            5800,
            600,
            5600,
            6200
        ),
    ])

    # ========================================================
    # CANOS
    # ========================================================

    canos.extend([

        Cano(
            930,
            600,
            100
        ),

        Cano(
            1950,
            600,
            130
        ),

        Cano(
            3050,
            600,
            110
        ),

        Cano(
            4150,
            600,
            140
        ),

        Cano(
            5450,
            600,
            110
        ),
    ])


# ============================================================
# NOVO JOGO
# ============================================================

def novo_jogo():

    global player
    global camera_x
    global pontuacao
    global moedas_coletadas
    global pausado
    global game_over
    global vitoria

    player = Player()

    camera_x = 0

    pontuacao = 0
    moedas_coletadas = 0

    pausado = False
    game_over = False
    vitoria = False

    particulas.clear()

    criar_fase()


# ============================================================
# MOEDAS
# ============================================================

def atualizar_moedas():

    global moedas_coletadas
    global pontuacao

    for moeda in moedas:

        if moeda.coletada:
            continue

        moeda.atualizar()

        if player.rect.colliderect(
            moeda.rect
        ):

            moeda.coletada = True

            moedas_coletadas += 1

            pontuacao += 100

            criar_particulas(
                moeda.x,
                moeda.y,
                10,
                AMARELO,
            )


# ============================================================
# INIMIGOS
# ============================================================

def atualizar_inimigos():

    global pontuacao

    for inimigo in inimigos:

        inimigo.atualizar()

        if not inimigo.vivo:
            continue

        if player.rect.colliderect(
            inimigo.rect
        ):

            # Luffy pulou em cima.
            if (
                player.vel_y > 0
                and
                player.rect.bottom
                <= inimigo.rect.top + 20
            ):

                inimigo.vivo = False

                player.vel_y = -11

                pontuacao += 250

                criar_particulas(
                    inimigo.x,
                    inimigo.y,
                    15,
                    ROXO,
                )

            else:

                player.dano()


# ============================================================
# CÂMERA
# ============================================================

def atualizar_camera():

    global camera_x

    alvo = (
        player.x -
        LARGURA * 0.35
    )

    camera_x += (
        alvo -
        camera_x
    ) * 0.10

    if camera_x < 0:
        camera_x = 0

    limite_camera = max(
        0,
        LARGURA_MUNDO -
        LARGURA
    )

    if camera_x > limite_camera:
        camera_x = limite_camera


# ============================================================
# QUEDA
# ============================================================

def verificar_queda():

    if player.y > 800:

        player.dano()

        if not player.morto:

            # Reposiciona antes do buraco.
            player.x = max(
                100,
                player.x - 250
            )

            player.y = 400

            player.vel_y = 0


# ============================================================
# FINAL DA FASE
# ============================================================

def desenhar_final():

    # Bandeira no final.
    x = int(
        6250 -
        camera_x
    )

    if (
        x < -100
        or
        x > LARGURA + 100
    ):
        return

    # Poste
    pygame.draw.rect(
        tela,
        (80, 80, 80),
        (
            x,
            360,
            8,
            240
        ),
    )

    # Bandeira
    pygame.draw.polygon(
        tela,
        VERMELHO,
        [
            (
                x + 8,
                365
            ),

            (
                x + 85,
                390
            ),

            (
                x + 8,
                415
            ),
        ],
    )

    texto(
        "FIM",
        fonte_pequena,
        BRANCO,
        (
            x + 35,
            335
        ),
        centro=True,
    )


def verificar_final():

    global vitoria

    if player.x >= 6250:

        vitoria = True


# ============================================================
# HUD
# ============================================================

def desenhar_hud():

    painel = pygame.Surface(
        (
            500,
            75
        ),
        pygame.SRCALPHA,
    )

    painel.fill(
        (
            0,
            0,
            0,
            110
        )
    )

    tela.blit(
        painel,
        (
            15,
            15
        ),
    )

    texto(
        f"VIDAS: {player.vidas}",
        fonte_hud,
        BRANCO,
        (
            30,
            28
        ),
    )

    texto(
        f"MOEDAS: {moedas_coletadas}",
        fonte_hud,
        AMARELO,
        (
            170,
            28
        ),
    )

    texto(
        f"PONTOS: {pontuacao}",
        fonte_hud,
        BRANCO,
        (
            350,
            28
        ),
    )

    texto(
        "A/D ou ← → mover | ESPAÇO/W/↑ pular | S/↓ abaixar | P pausar",
        fonte_pequena,
        BRANCO,
        (
            LARGURA // 2,
            ALTURA - 20
        ),
        centro=True,
    )


# ============================================================
# MENU
# ============================================================

def desenhar_menu():

    overlay = pygame.Surface(
        (
            LARGURA,
            ALTURA
        ),
        pygame.SRCALPHA,
    )

    overlay.fill(
        (
            0,
            20,
            40,
            120
        )
    )

    tela.blit(
        overlay,
        (
            0,
            0
        ),
    )

    texto(
        "CRASH",
        fonte_grande,
        AMARELO,
        (
            LARGURA // 2,
            180
        ),
        centro=True,
    )

    texto(
        "ADVENTURE",
        fonte_grande,
        BRANCO,
        (
            LARGURA // 2,
            255
        ),
        centro=True,
    )

    texto(
        "UMA AVENTURA DO CRASH",
        fonte_hud,
        BRANCO,
        (
            LARGURA // 2,
            340
        ),
        centro=True,
    )

    texto(
        "ESPAÇO ou ENTER para começar",
        fonte_media,
        AMARELO,
        (
            LARGURA // 2,
            430
        ),
        centro=True,
    )

    texto(
        "← → mover | ESPAÇO pular | ↓ abaixar",
        fonte_pequena,
        BRANCO,
        (
            LARGURA // 2,
            500
        ),
        centro=True,
    )


# ============================================================
# PAUSA
# ============================================================

def desenhar_pausa():

    overlay = pygame.Surface(
        (
            LARGURA,
            ALTURA
        ),
        pygame.SRCALPHA,
    )

    overlay.fill(
        (
            0,
            0,
            0,
            150
        )
    )

    tela.blit(
        overlay,
        (
            0,
            0
        ),
    )

    texto(
        "PAUSADO",
        fonte_grande,
        BRANCO,
        (
            LARGURA // 2,
            300
        ),
        centro=True,
    )

    texto(
        "Pressione P para continuar",
        fonte_media,
        AMARELO,
        (
            LARGURA // 2,
            400
        ),
        centro=True,
    )


# ============================================================
# GAME OVER
# ============================================================

def desenhar_game_over():

    overlay = pygame.Surface(
        (
            LARGURA,
            ALTURA
        ),
        pygame.SRCALPHA,
    )

    overlay.fill(
        (
            0,
            0,
            0,
            180
        )
    )

    tela.blit(
        overlay,
        (
            0,
            0
        ),
    )

    texto(
        "GAME OVER",
        fonte_grande,
        VERMELHO,
        (
            LARGURA // 2,
            220
        ),
        centro=True,
    )

    texto(
        f"PONTOS: {pontuacao}",
        fonte_media,
        BRANCO,
        (
            LARGURA // 2,
            320
        ),
        centro=True,
    )

    texto(
        f"MOEDAS: {moedas_coletadas}",
        fonte_hud,
        AMARELO,
        (
            LARGURA // 2,
            380
        ),
        centro=True,
    )

    texto(
        "R ou ESPAÇO para jogar novamente",
        fonte_media,
        BRANCO,
        (
            LARGURA // 2,
            460
        ),
        centro=True,
    )


# ============================================================
# VITÓRIA
# ============================================================

def desenhar_vitoria():

    overlay = pygame.Surface(
        (
            LARGURA,
            ALTURA
        ),
        pygame.SRCALPHA,
    )

    overlay.fill(
        (
            0,
            40,
            10,
            180
        )
    )

    tela.blit(
        overlay,
        (
            0,
            0
        ),
    )

    texto(
        "FASE CONCLUÍDA!",
        fonte_grande,
        AMARELO,
        (
            LARGURA // 2,
            220
        ),
        centro=True,
    )

    texto(
        "Você chegou ao final da fase!",
        fonte_media,
        BRANCO,
        (
            LARGURA // 2,
            320
        ),
        centro=True,
    )

    texto(
        f"Pontos: {pontuacao}",
        fonte_hud,
        AMARELO,
        (
            LARGURA // 2,
            380
        ),
        centro=True,
    )

    texto(
        "R ou ESPAÇO para jogar novamente",
        fonte_media,
        BRANCO,
        (
            LARGURA // 2,
            460
        ),
        centro=True,
    )


# ============================================================
# INICIALIZAÇÃO
# ============================================================

novo_jogo()


# ============================================================
# LOOP PRINCIPAL
# ============================================================

rodando = True

while rodando:

    clock.tick(FPS)

    # ========================================================
    # EVENTOS
    # ========================================================

    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:

            rodando = False

        if evento.type == pygame.KEYDOWN:

            if evento.key == pygame.K_ESCAPE:

                rodando = False

            # =================================================
            # MENU
            # =================================================

            if not jogo_iniciado:

                if evento.key in (
                    pygame.K_SPACE,
                    pygame.K_RETURN,
                ):

                    jogo_iniciado = True

            # =================================================
            # GAME OVER
            # =================================================

            elif player.morto:

                if evento.key in (
                    pygame.K_r,
                    pygame.K_SPACE,
                    pygame.K_RETURN,
                ):

                    novo_jogo()

            # =================================================
            # VITÓRIA
            # =================================================

            elif vitoria:

                if evento.key in (
                    pygame.K_r,
                    pygame.K_SPACE,
                    pygame.K_RETURN,
                ):

                    novo_jogo()

            # =================================================
            # JOGO
            # =================================================

            else:

                if evento.key == pygame.K_p:

                    pausado = not pausado

                if not pausado:

                    if evento.key in (
                        pygame.K_SPACE,
                        pygame.K_UP,
                        pygame.K_w,
                    ):

                        player.pular()

    # ========================================================
    # ATUALIZAÇÃO
    # ========================================================

    if (
        jogo_iniciado
        and not pausado
        and not player.morto
        and not vitoria
    ):

        player.atualizar()

        atualizar_moedas()

        atualizar_inimigos()

        verificar_queda()

        verificar_final()

        atualizar_camera()

        atualizar_particulas()

        # Pontuação conforme avanço.
        pontuacao = max(
            pontuacao,
            int(
                player.x / 5
            )
            +
            moedas_coletadas * 100
        )

    # ========================================================
    # DESENHO
    # ========================================================

    desenhar_fundo()

    # Plataformas
    for plataforma in plataformas:

        plataforma.desenhar()

    # Canos
    for cano in canos:

        cano.desenhar()

    # Blocos
    for bloco in blocos:

        bloco.desenhar()

    # Moedas
    for moeda in moedas:

        moeda.desenhar()

    # Inimigos
    for inimigo in inimigos:

        inimigo.desenhar()

    # Linha de chegada
    desenhar_final()

    # Luffy
    player.desenhar()

    # Partículas
    desenhar_particulas()

    # HUD
    if jogo_iniciado:

        desenhar_hud()

    # Menu
    if not jogo_iniciado:

        desenhar_menu()

    # Pausa
    elif pausado:

        desenhar_pausa()

    # Game Over
    elif player.morto:

        game_over = True

        desenhar_game_over()

    # Vitória
    elif vitoria:

        desenhar_vitoria()

    pygame.display.flip()


# ============================================================
# ENCERRAR
# ============================================================

pygame.quit()
sys.exit()