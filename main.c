#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BLOCK_SIZE 512
#define DNODE_SIZE 64
#define MAX_FILES 10
#define MAX_BLOCKS 100


typedef struct {
    int size;
    int free_blocks;
    int first_free_block;
    char spacemap[MAX_BLOCKS]; 
} uberblock_t;


typedef struct {
    char filename[32];
    int size;
    int first_block;
    int next_block;
    unsigned long checksum; // O GRANDE DIFERENCIAL DO ZFS
} dnode_t;

// funções auxiliares abaixo

// Função Checksum serve para garantir integridade

unsigned long calcular_checksum(const char *data) {
    unsigned long sum = 0;
    for (int i = 0; data[i] != '\0'; ++i) sum += data[i];
    return sum;
}

// Procura um bloco que esteja livre no Pool

int find_free_block(FILE *disk) {
    uberblock_t sb;
    fseek(disk, 0, SEEK_SET);
    fread(&sb, sizeof(uberblock_t), 1, disk);
    
    // Função para procurar no Spacemap

    for (int i = 0; i < MAX_BLOCKS; i++) {
        if (sb.spacemap[i] == 0) { // O 0 significa que está livre
            sb.spacemap[i] = 1;    // O 1 significa que está ocupado
            sb.free_blocks--;
            fseek(disk, 0, SEEK_SET);
            fwrite(&sb, sizeof(uberblock_t), 1, disk);
            return i;
        }
    }
    return -1;
}

// Serve para encontrar um slot de arquivo livre

int find_free_dnode(FILE *disk) {
    dnode_t node;
    for (int i = 0; i < MAX_FILES; i++) {
        fseek(disk, sizeof(uberblock_t) + i * sizeof(dnode_t), SEEK_SET);
        fread(&node, sizeof(dnode_t), 1, disk);
        if (node.filename[0] == '\0') {
            return i;
        }
    }
    return -1;
}

// Serve para inicializa o Zpool

void init_zpool(FILE *disk) {
    uberblock_t sb = {BLOCK_SIZE * MAX_BLOCKS, MAX_BLOCKS, 0, {0}};
    fwrite(&sb, sizeof(uberblock_t), 1, disk);

    dnode_t empty_node = {"", 0, -1, -1, 0};
    for (int i = 0; i < MAX_FILES; i++) {
        fwrite(&empty_node, sizeof(dnode_t), 1, disk);
    }
    printf("[ZFS] Zpool inicializado e Uberblock criado.\n");
}

// -- operação crud --

// Função para cria um arquivo

int create_file(FILE *disk, char *filename) {
    int node_index = find_free_dnode(disk);
    if (node_index == -1) return -1;

    dnode_t new_node = {0};
    strcpy(new_node.filename, filename);
    new_node.first_block = -1; // Inicializa sem blocos

    fseek(disk, sizeof(uberblock_t) + node_index * sizeof(dnode_t), SEEK_SET);
    fwrite(&new_node, sizeof(dnode_t), 1, disk);
    return node_index;
}

// Serve para escrever no arquivo 

int write_file(FILE *disk, char *filename, char *data, int size) {
    dnode_t node;
    int node_index = -1;

    // Serve para busca o arquivo

    for (int i = 0; i < MAX_FILES; i++) {
        fseek(disk, sizeof(uberblock_t) + i * sizeof(dnode_t), SEEK_SET);
        fread(&node, sizeof(dnode_t), 1, disk);
        if (strcmp(node.filename, filename) == 0) {
            node_index = i;
            break;
        }
    }
    if (node_index == -1) return -1;

    // Serve para calcular o Checksum antes de gravar

    node.checksum = calcular_checksum(data);

    // Serve para a lógica de alocação de blocos

    int block_idx = find_free_block(disk);
    if(block_idx == -1) return -1;

    // Função para grava dados no bloco

    fseek(disk, sizeof(uberblock_t) + MAX_FILES * sizeof(dnode_t) + block_idx * BLOCK_SIZE, SEEK_SET);
    fwrite(data, 1, size, disk);

    // Serve para atualiza o Dnode

    node.first_block = block_idx;
    node.size = size;
    
    fseek(disk, sizeof(uberblock_t) + node_index * sizeof(dnode_t), SEEK_SET);
    fwrite(&node, sizeof(dnode_t), 1, disk);

    return size;
}

// Lê arquivo e verifica sua integridade

int read_file(FILE *disk, char *filename, char *buffer) {
    dnode_t node;
    int node_index = -1;

    for (int i = 0; i < MAX_FILES; i++) {
        fseek(disk, sizeof(uberblock_t) + i * sizeof(dnode_t), SEEK_SET);
        fread(&node, sizeof(dnode_t), 1, disk);
        if (strcmp(node.filename, filename) == 0) {
            node_index = i;
            break;
        }
    }
    if (node_index == -1) {
        printf("Erro: Arquivo não encontrado.\n");
        return -1;
    }

    if (node.first_block != -1) {
        fseek(disk, sizeof(uberblock_t) + MAX_FILES * sizeof(dnode_t) + node.first_block * BLOCK_SIZE, SEEK_SET);
        fread(buffer, 1, node.size, disk);
        buffer[node.size] = '\0';

        // EXECUTA A VERIFICAÇÃO DO ZFS

        unsigned long check_atual = calcular_checksum(buffer);
        if(check_atual == node.checksum) {
            printf("[ZFS INTEGRITY] Checksum OK (%lu). Dados válidos.\n", check_atual);
        } else {
            printf("[ZFS ALERTA] CORRUPÇÃO DE DADOS DETECTADA!\n");
        }
    }
    return node.size;
}

// A função para deletar arquivos

void delete_file(FILE *disk, char *filename) {
    dnode_t node;
    uberblock_t sb;
    int node_index = -1;

    // Faz a leitura do Uberblock para atualizar o spacemap

    fseek(disk, 0, SEEK_SET);
    fread(&sb, sizeof(uberblock_t), 1, disk);

    // Função para achar o arquivo

    for (int i = 0; i < MAX_FILES; i++) {
        fseek(disk, sizeof(uberblock_t) + i * sizeof(dnode_t), SEEK_SET);
        fread(&node, sizeof(dnode_t), 1, disk);
        if (strcmp(node.filename, filename) == 0) {
            node_index = i;
            break;
        }
    }

    if (node_index == -1) {
        printf("Arquivo não encontrado.\n");
        return;
    }

    // Função para liberar o bloco no Spacemap

    if (node.first_block != -1) {
        sb.spacemap[node.first_block] = 0; // Marca como livre
        sb.free_blocks++;
    }

    // Serve para limpar o Dnode

    dnode_t empty = {"", 0, -1, -1, 0};
    fseek(disk, sizeof(uberblock_t) + node_index * sizeof(dnode_t), SEEK_SET);
    fwrite(&empty, sizeof(dnode_t), 1, disk);

    // Serve para atualizar Uberblock no disco
    fseek(disk, 0, SEEK_SET);
    fwrite(&sb, sizeof(uberblock_t), 1, disk);

    printf("Arquivo '%s' deletado e blocos liberados no Pool.\n", filename);
}

// A lista dos arquivos

void list_files(FILE *disk) {
    dnode_t node;
    printf("\n--- ARQUIVOS NO ZPOOL ---\n");
    for (int i = 0; i < MAX_FILES; i++) {
        fseek(disk, sizeof(uberblock_t) + i * sizeof(dnode_t), SEEK_SET);
        fread(&node, sizeof(dnode_t), 1, disk);
        if (node.filename[0] != '\0') {
            printf("Arquivo: %s | Tamanho: %d | Checksum: %lu\n", node.filename, node.size, node.checksum);
        }
    }
    printf("-------------------------\n");
}

int main() {
    FILE *disk = fopen("zfs_disk.bin", "w+b"); // Cria arquivo do disco
    if (!disk) {
        printf("Erro ao criar disco virtual.\n");
        return 1;
    }

    init_zpool(disk);

    char command[16], filename[32], data[BLOCK_SIZE];

    while (1) {
        printf("\nZFS Shell> ");
        scanf("%s", command);

        if (strcmp(command, "create") == 0) {
            scanf("%s", filename);
            create_file(disk, filename);
        } else if (strcmp(command, "write") == 0) {
            scanf("%s %[^\n]", filename, data);
            write_file(disk, filename, data, strlen(data));
        } else if (strcmp(command, "read") == 0) {
            scanf("%s", filename);
            if(read_file(disk, filename, data) != -1) {
                printf("Conteúdo: %s\n", data);
            }
        } else if (strcmp(command, "list") == 0) {
            list_files(disk);
        } else if (strcmp(command, "delete") == 0) {
            scanf("%s", filename);
            delete_file(disk, filename);
        } else if (strcmp(command, "exit") == 0) {
            break;
        } else {
            printf("Comandos: create, write, read, list, delete, exit\n");
        }
    }

    fclose(disk);
    return 0;
}
