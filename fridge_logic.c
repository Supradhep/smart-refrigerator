#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdbool.h>

#define MAX_INGREDIENTS 100
#define DATE_FORMAT "%Y-%m-%d"

typedef struct {
    char name[100];
    float quantity;
    char unit[20];
    char added_date[20];
    int expires_in;
} Ingredient;

Ingredient ingredients[MAX_INGREDIENTS];
Ingredient singredients[MAX_INGREDIENTS];
int ingredient_count = 0;
int singredient_count = 0;

int is_duplicate(const char *name) {
    for (int i = 0; i < ingredient_count; i++) {
        if (strcmp(ingredients[i].name, name) == 0) {
            return 1;
        }
    }
    return 0;
}

void add_ingredient(const char *name, float quantity, const char *unit, int expires_in) {
    if (ingredient_count >= MAX_INGREDIENTS) {
        printf("Error: Storage limit reached.\n");
        return;
    }

    if (is_duplicate(name)) {
        printf("Ingredient exists: %s\n", name);
        return;
    }

    time_t now = time(NULL);
    struct tm *tm = localtime(&now);
    strftime(ingredients[ingredient_count].added_date, 20, DATE_FORMAT, tm);

    strcpy(ingredients[ingredient_count].name, name);
    ingredients[ingredient_count].quantity = quantity;
    strcpy(ingredients[ingredient_count].unit, unit);
    ingredients[ingredient_count].expires_in = expires_in;
    ingredient_count++;

    FILE *file = fopen("ingredients.txt", "a");
    if (file) {
        fprintf(file, "%s|%.2f|%s|%s|%d\n", name, quantity, unit,
                ingredients[ingredient_count-1].added_date, expires_in);
        fclose(file);
    }
    printf("Added: %s (%.2f %s), expires in %d days\n", name, quantity, unit, expires_in);
}

void take_ingredient(const char *name, float quantity) {
    int found = 0;
    for (int i = 0; i < ingredient_count; i++) {
        if (strcmp(ingredients[i].name, name) == 0) {
            found = 1;
            if (quantity >= ingredients[i].quantity) {
                for (int j = i; j < ingredient_count-1; j++) {
                    ingredients[j] = ingredients[j+1];
                }
                ingredient_count--;
                printf("Removed: %s\n", name);
            } else {
                ingredients[i].quantity -= quantity;
                printf("Took %.2f %s of %s (remaining: %.2f)\n",
                      quantity, ingredients[i].unit, name, ingredients[i].quantity);
            }
            break;
        }
    }

    if (!found) {
        printf("Not found: %s\n", name);
        return;
    }

    FILE *file = fopen("ingredients.txt", "w");
    if (file) {
        for (int i = 0; i < ingredient_count; i++) {
            fprintf(file, "%s|%.2f|%s|%s|%d\n",
                    ingredients[i].name, ingredients[i].quantity,
                    ingredients[i].unit, ingredients[i].added_date,
                    ingredients[i].expires_in);
        }
        fclose(file);
    }
}

void load_ingredients() {
    FILE *file = fopen("ingredients.txt", "r");
    if (file) {
        char line[256];
        while (fgets(line, sizeof(line), file)) {
            char *name = strtok(line, "|");
            char *qty = strtok(NULL, "|");
            char *unit = strtok(NULL, "|");
            char *date = strtok(NULL, "|");
            char *exp = strtok(NULL, "|");

            if (name && qty && unit && date && exp) {
                strcpy(ingredients[ingredient_count].name, name);
                ingredients[ingredient_count].quantity = atof(qty);
                strcpy(ingredients[ingredient_count].unit, unit);
                strcpy(ingredients[ingredient_count].added_date, date);
                ingredients[ingredient_count].expires_in = atoi(exp);
                ingredient_count++;
            }
        }
        fclose(file);
    }
}

void load_singredients() {
    FILE *file = fopen("singredients.txt", "r");
    if (file) {
        char line[256];
        while (fgets(line, sizeof(line), file)) {
            char *name = strtok(line, "|");
            char *qty = strtok(NULL, "|");
            char *unit = strtok(NULL, "|");
            char *date = strtok(NULL, "|");
            char *exp = strtok(NULL, "|");

            if (name) {
                strcpy(singredients[singredient_count].name, name);
                if (qty) singredients[singredient_count].quantity = atof(qty);
                if (unit) strcpy(singredients[singredient_count].unit, unit);
                if (date) strcpy(singredients[singredient_count].added_date, date);
                if (exp) singredients[singredient_count].expires_in = atoi(exp);
                singredient_count++;
            }
        }
        fclose(file);
    }
}

bool is_in_ingredients(const char *name) {
    for (int i = 0; i < ingredient_count; i++) {
        if (strcmp(ingredients[i].name, name) == 0) {
            return true;
        }
    }
    return false;
}

void generate_shopping_list() {
    FILE *html_file = fopen("shopping_list.html", "w");
    if (!html_file) {
        printf("Error creating shopping list file.\n");
        return;
    }

    // HTML header
    fprintf(html_file, "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n");
    fprintf(html_file, "    <title>Smart Refrigerator - Shopping List</title>\n");
    fprintf(html_file, "    <link rel=\"stylesheet\" href=\"refrigerator.css\">\n");
    fprintf(html_file, "</head>\n<body>\n");
    fprintf(html_file, "    <header>\n        <h1>Shopping List</h1>\n    </header>\n");
    fprintf(html_file, "    <div class=\"container\">\n");
    fprintf(html_file, "        <section class=\"btn\">\n");
    fprintf(html_file, "            <a href=\"home.html\" style=\"text-decoration: none;\">Go to Home</a>\n");
    fprintf(html_file, "        </section>\n\n");

    // Items to restock (quantity < 1 and expires in 2 days)
    fprintf(html_file, "        <div class=\"shopping-list\">\n");
    fprintf(html_file, "            <h2>Items to Restock (low quantity/expiring soon):</h2>\n");
    fprintf(html_file, "            <ul>\n");

    int restock_count = 0;
    for (int i = 0; i < ingredient_count; i++) {
        if ((strcmp(ingredients[i].unit, "kg") == 0 && ingredients[i].quantity < 1.0) ||
            (strcmp(ingredients[i].unit, "liter") == 0 && ingredients[i].quantity < 1.0) ||
            ingredients[i].expires_in <= 2) {
            fprintf(html_file, "                <li>%s (%.2f %s, expires in %d days)</li>\n",
                   ingredients[i].name, ingredients[i].quantity, 
                   ingredients[i].unit, ingredients[i].expires_in);
            restock_count++;
        }
    }
    if (restock_count == 0) {
        fprintf(html_file, "                <li>No items need restocking</li>\n");
    }

    fprintf(html_file, "            </ul>\n        </div>\n\n");

    // Standard shopping items (from singredients.txt not in ingredients.txt)
    fprintf(html_file, "        <div class=\"shopping-list\">\n");
    fprintf(html_file, "            <h2>Standard Shopping Items:</h2>\n");
    fprintf(html_file, "            <ul>\n");

    int standard_count = 0;
    for (int i = 0; i < singredient_count; i++) {
        if (!is_in_ingredients(singredients[i].name)) {
            fprintf(html_file, "                <li>%s</li>\n", singredients[i].name);
            standard_count++;
        }
    }
    if (standard_count == 0) {
        fprintf(html_file, "                <li>No standard items needed</li>\n");
    }

    fprintf(html_file, "            </ul>\n        </div>\n");

    // HTML footer
    fprintf(html_file, "    </div>\n</body>\n</html>");
    fclose(html_file);

    printf("Shopping list generated: shopping_list.html\n");
}

int main(int argc, char *argv[]) {
    load_ingredients();
    load_singredients();

    if (argc > 1) {
        if (strcmp(argv[1], "add") == 0 && argc >= 6) {
            add_ingredient(argv[2], atof(argv[3]), argv[4], atoi(argv[5]));
        } else if (strcmp(argv[1], "take") == 0 && argc >= 4) {
            take_ingredient(argv[2], atof(argv[3]));
        } else if (strcmp(argv[1], "shopping") == 0) {
            generate_shopping_list();
        } else {
            printf("Usage:\n");
            printf(" add <name> <quantity> <unit> <expires_in_days>\n");
            printf(" take <name> <quantity>\n");
            printf(" shopping - generate shopping list\n");
        }
    } else {
        printf("No command provided.\n");
    }

    return 0;
}