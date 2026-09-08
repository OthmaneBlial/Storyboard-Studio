# Storyboard Studio — roadmap vers une publication crédible

Audit initial du **8 septembre 2026**, sur `main`, commit de référence
**`0b4adbb74a3b8996dd3be6b071a0a0a98f71ec1b`**. Le suivi d'exécution de ce
roadmap est versionné sur `main`; la dernière preuve d'artefact documentée est
le commit **`919808b`**, avec des artefacts construits depuis `45959d4`. Les constats
historiques ci-dessous restent datés lorsqu'ils décrivent un défaut déjà
corrigé.

Ce document remplace l'ancien roadmap, dont certaines prochaines tâches étaient déjà implémentées. Il distingue les capacités présentes, les défauts reproduits et les validations encore nécessaires. **Instantané initial :** seul le roadmap avait été modifié à la fin de l’audit. L’implémentation est maintenant autorisée ; les résultats et validations sont suivis ci-dessous. Les constats d’audit restent datés et ne décrivent pas automatiquement l’état corrigé.

## Verdict

Le projet possède un angle utile : **transformer un brief de décision privé en argument révisable, puis en PowerPoint éditable accompagné d'un reçu d'intégrité**. Le compilateur local, le Narrative Doctor, les sources par affirmation et l'interchange JSON/Markdown forment un ensemble plus distinctif qu'un générateur de diapositives générique.

Le principal manque n'est pas une nouvelle collection de fonctionnalités. C'est la continuité entre **promesse, résultat, sauvegarde, preuve, installation et version distribuée**. Lors de l'audit initial, les trois reçus mis en avant dans la galerie échouaient avec le vérificateur, le nettoyage du serveur pouvait supprimer des fichiers qu'il n'avait pas créés, et PyPI renvoyait 404. Ces problèmes compromettaient davantage la confiance qu'un manque de thèmes ; les corrections locales sont suivies par phase ci-dessous.

L'identité visuelle mérite d'être conservée. L'effort UX doit surtout réduire le nombre de décisions demandées au démarrage, rendre l'édition et la sauvegarde explicites, et rapprocher l'aperçu des objets réellement exportés. L'adoption reste une hypothèse : le dépôt documente 0/10 sessions utilisateurs et 0/5 workflows réels, pas des résultats externes.

Les stars sont un indicateur secondaire. Aucune quantité de stars ni viralité ne peut être garantie par l'exécution de ce plan.

### État d'exécution au 8 septembre 2026

Les corrections locales déjà poussées sur `main` couvrent les reçus et la
galerie, le cache serveur et ses limites, le brief guidé, la sauvegarde et les
assets portables, les projections de blocs sémantiques, les preuves LibreOffice
archivées, l'activation des workflows et la documentation d'installation.
Un run CI complet vérifié (`34217088673`, commit `a85dd8c`) est vert sur Python
3.10–3.14, packaging, navigateur et benchmark ; le job visuel reste skipped.
Les actions externes des workflows actifs et des snapshots conservés sont
désormais épinglées sur des commits immuables vérifiés, avec le tag lisible en
commentaire ; Dependabot reste le mécanisme mensuel de mise à jour. Le snapshot
CI historique peut différer de l'actif (par exemple `make test` au lieu de la
couverture), et cette différence est documentée plutôt que présentée comme une
copie exécutable identique.
Les contrats Python et le planificateur fournisseur sont maintenant canoniques
dans `storyboard_studio.schemas` et `storyboard_studio.ai_helper` ; `schemas.py`
et `ai_helper.py` ne font plus que préserver les imports historiques. Des tests
vérifient l'identité des classes et fonctions entre les chemins. Les imports de
production utilisent les modules packagés ; le renderer, le serveur et les
autres modules racine restent à traiter, ainsi que l'équivalence complète des
corpus.
La validation d'installation du wheel et
du sdist, avec et sans extras `gemini,svg`, est passée sur macOS ARM64/Python
3.14 ; le SBOM, les checksums et le contrôle des archives passent localement.
Ces preuves ne ferment pas les gates qui nécessitent Docker, Windows/Linux,
PowerPoint/Keynote/Google Slides, des utilisateurs externes, une publication
PyPI/GitHub ou la vidéo finale.

## État vérifié et limites de l'audit

### Inventaire du produit

| Surface | Présent dans le dépôt | Manque ou limite concrète |
| --- | --- | --- |
| Parcours principal | Brief structuré, compilation locale en cinq diapositives de contenu, révision, Doctor, export | Formulaire initial long ; comparaison limitée aux deux premières options ; un seul critère construit depuis le premier compromis ; titres et transitions fixes |
| Éditeur | Canvas 16:9, Outline, zoom, édition, ajout/duplication/réordonnancement, undo/redo, sources, import/export | État essentiellement en mémoire ; avertissement de fermeture mais pas de récupération persistante ; la sauvegarde éditable est distincte du PPTX |
| Sémantique | Blocs standard, comparaison, décision, timeline, métrique, processus, citation, table, graphique, image | Les graphiques/images demandent des assets déjà décrits et accessibles au serveur ; pas de parcours simple de sélection/import des assets dans le navigateur |
| Sorties | PPTX natif, JSON/Markdown, bundle et reçu ; graphiques et tables natifs | Aperçu sémantique, pas rendu Office fidèle ; le bundle ne contient que PPTX, story et receipt, pas les assets nécessaires à une régénération indépendante |
| Confidentialité | Local par défaut, fournisseurs explicites, CSP, schémas stricts, contrôle des chemins et empreintes d'assets | Durée de conservation et limite HTTP incomplètement appliquées ; absence d'authentification pour une exposition réseau ; contexte Docker à resserrer |
| Intégrations | CLI, API FastAPI, Action composite de revue, serveur JSONL, exemples | Le serveur JSONL n'est pas à présenter comme un serveur MCP conforme ; plusieurs validateurs parallèles à maintenir |
| Documentation | README, architecture, sécurité, contribution, migration, galerie, benchmark, matrice viewers | Documentation abondante, frontières release/main parfois confuses, preuves vieillissantes, parcours Windows peu accessible |
| Distribution | `pyproject.toml`, ressources embarquées, wheel/sdist, Dockerfile, workflows conservés | Pas de package PyPI public constaté, ni installateur natif dans la dernière release ; installation du Dockerfile et des paquets sur les trois OS non validée ici |

Sources principales : `schemas.py`, `storyboard_studio/story.py`, `doctor.py`, `receipt.py`, `assets.py`, `providers.py`, `tool_server.py`, `cli.py`, `generate_pptx.py`, `server.py`, `storyboard_studio/web/`, `docs/`.

### Validations réellement exécutées

L'environnement du checkout n'avait pas de `.venv`. Une archive du commit a été extraite sous `/tmp`, puis installée avec ses extras `dev,browser` dans un environnement isolé. Aucun test n'a écrit dans les sources du dépôt de travail. Ces résultats concernent **macOS ARM64, Python 3.14**, pas toute la matrice annoncée.

| Vérification | Résultat de cet audit |
| --- | --- |
| Installation de la copie avec `pip install -e '.[dev,browser]'` | Réussie ; ce n'est pas une installation propre d'un wheel distribué |
| `make lint format-check` | Réussi, 120 fichiers Python correctement formatés |
| `make test` | **104 tests réussis**, un avertissement de dépréciation Starlette/AnyIO |
| `make browser-test` | **9 scénarios Chromium réussis**, incluant clavier, import, export, sources, assets et responsive |
| `make validate-assets validate-site validate-layout validate-viewer-reports` | Réussi ; le dernier contrôle vérifie des rapports existants, pas un nouveau rendu Office |
| `make smoke` | Réussi : API locale → export PPTX, 35 696 octets |
| `make benchmark-check` | Réussi contre la baseline locale ; benchmark synthétique, aucune mesure comparative d'utilité humaine |
| `python -m build` | Wheel et sdist construits ; installation de chacun hors checkout non exécutée ici |
| Navigateur interactif | Accueil et studio inspectés après reconnexion ; exemple compilé, Doctor exécuté, titre sélectionné ; aucune erreur console relevée sur ce parcours |
| Vitrine publique | HTTP 200 et contenu identique au dépôt pour `index.html`, `docs.html`, `styles.css` et `app.js` ; le test responsive de la vitrine a été exécuté localement |
| Office | Pas de nouvelle ouverture/édition PowerPoint ou LibreOffice pendant cet audit |
| Ancienne vidéo | Fichier présent, `ffprobe` : 24,766667 s, 1200 × 666, H.264, yuv420p, 60 i/s, 1 439 328 octets, sans piste audio ; lecture intégrale non revérifiée |

Après rédaction, les quatre tests de `tests/test_launch.py` ont également été rejoués avec ce nouveau document : réussite. `git diff --check` ne signale aucune erreur. Pour reproduire le défaut de galerie après installation, exécuter `storyboard verify gallery/onboarding-pilot/deck.receipt.json`, puis les deux autres reçus cités en A4. Les autres reproductions utilisent exclusivement des fichiers synthétiques dans un répertoire temporaire ; ne pas tester la purge sur le véritable dossier de travail.

La capture de l'accueil montre une identité éditoriale cohérente : fond crème, vert sombre, serif, accents dorés. Le studio conserve un long empilement : provenance, sources, preflight, couverture, Doctor, puis diapositives. L'aperçu du titre reste très vide et ses champs visibles donnent une impression d'éditeur de formulaire. Il faut tester ces choix auprès d'auteurs réels, pas conclure que le produit est inutilisable à partir de son seul aspect.

### Défauts reproduits et constats de code

| ID | Priorité | Preuve et conséquence | Destination |
| --- | --- | --- | --- |
| A1 | P0 | Dans un dossier temporaire, `_cleanup_exports()` supprime `user-owned.pptx` âgé de plus de 24 h. La sélection porte sur tous les `*.pptx`/`*.zip`, contrairement à sa docstring. `output/` sert aussi aux exports CLI. | 1.1 |
| A2 | P0 | Une requête JSON valide de **210 069 octets**, envoyée par itérateur sans `Content-Length`, reçoit HTTP 200 sur `/api/v1/content`. Le middleware ne compte pas les octets reçus. | 1.2 |
| A3 | P0 | Un export au nom valide et vieux de plus de 24 h reste téléchargeable en HTTP 200. Nettoyage au démarrage et avant export seulement ; aucune vérification d'âge au téléchargement. | 1.1 |
| A4 | P0 | Les trois `gallery/{onboarding-pilot,privacy-analytics,recovery-drill}/deck.receipt.json` renvoient `invalid` : « The story outline digest does not match the receipt. » Les hashes des fichiers passent ; la normalisation actuelle ajoute notamment `content_block`, champs de sources, `assets`, `brand_kit`, `citations_appendix`. L'empreinte enregistrée correspond au payload brut historique. | 0.2 |
| A5 | P0 | Un reçu fraîchement généré est `verified`. Après modification de `doctor` et `source_coverage` seulement, il reste `verified`. `verify_receipt()` vérifie les artefacts et une partie du contrat, pas la cohérence de toutes les métadonnées présentées comme preuve. | 0.2 |
| A6 | P1 | `downloadButton` remet `state.dirty` à false après déclenchement du lien PPTX ; ce format ne permet pas de reprendre toute la story dans l'application. Le bundle ne suit pas le même état de sauvegarde. | 3.2 |
| A7 | P1 | Le bouton PPTX appelle le preflight ; le bouton bundle ne le fait pas. `create_presentation()` n'appelle pas `analyze_overflow`. L'application ne doit pas présenter la même garantie pour ces chemins sans contrat commun. | 4.1 |
| A8 | P1 | `.dockerignore` exclut `output/*.pptx`, mais pas tous les ZIP/story/receipts de `output/`. Avec `COPY . .`, des exports locaux peuvent entrer dans l'image. Aucun fichier privé n'a été utilisé pour ce constat. | 1.3 |
| A9 | P1 | `launch.py` accepte un tag sur comparaison de chaînes, lit des fragments de YAML/Markdown et reconnaît une capacité de maintenance par des mots dans le roadmap. Un workflow en pause peut être signalé `passed`. Ce n'est pas une preuve d'exécution/publication. | 0.1, 7.2 |
| A10 | P1 | `tests/test_launch.py` exige exactement 11 cases non cochées du roadmap réel et un état de lancement bloqué. Des tests éditoriaux figent aussi du texte du site/README. Le test peut casser pour une mise à jour documentaire légitime. | 5.2 |

Autres risques issus de lecture, **non démontrés comme exploits** : redirections/proxies de `urllib.request.urlopen` dans l'adaptateur annoncé loopback-only ; SVG rasterisé avant borne explicite de surface ; concurrence d'exports et taille des réponses fournisseurs peu bornées ; imports Python directs de CairoSVG/Pillow et modules racine génériques. Ils justifient des tests ciblés, pas une affirmation de compromission.

### GitHub et publications

Vérifications en lecture seule via GitHub CLI/API le 8 septembre 2026 :

- [Dépôt](https://github.com/OthmaneBlial/Storyboard-Studio) : 1 star, 0 fork ; description, homepage et 14 topics renseignés. Ces chiffres sont un instantané, pas une mesure d'activation.
- [Dernière release](https://github.com/OthmaneBlial/Storyboard-Studio/releases/tag/v0.2.0) : publiée le 26 août 2026 ; wheel de 17 902 octets et sdist de 21 273 octets, un téléchargement chacun. Ni installateur natif, ni `SHA256SUMS`/SBOM attachés à cette release. Ne pas confondre les digests fournis par GitHub avec un manifeste de release.
- `main` est actuellement 78 commits après `v0.2.0` ; les métadonnées du package restent `0.2.0`. Il existe des releases : c'est **la livraison du produit actuel** qui manque.
- [Endpoint PyPI](https://pypi.org/pypi/storyboard-studio/json) : HTTP 404. Propriété du nom et configuration du Trusted Publisher non confirmées.
- Au début de l'audit, `.github/workflows-disabled/` contenait CI/release/revue et `.github/workflows/` ne contenait que son README ; les workflows ont depuis été restaurés et sont actifs. La pause historique reste conservée comme référence d'audit.
- La protection de `main` exige `verify (3.10)` à `verify (3.14)` et `package`, en mode strict. Ces contrôles sont maintenant produits par le workflow actif ; les administrateurs ne sont pas soumis à cette protection.
- Huit issues ouvertes pour démarrer/contribuer sont vérifiées, dont quatre avec `good first issue`. Le compteur API de 10 inclut également les pull requests : ne pas le présenter comme dix issues d'utilisateurs.
- Discussions est activé. La disponibilité réelle du mainteneur, des retours clients, la configuration du social preview et l'ensemble des paramètres de sécurité n'ont pas été validés ici.

Les définitions CI sont déjà substantielles : tests, package hors checkout, navigateur, benchmark et rendu LibreOffice manuel. Elles tournent sur Ubuntu, pas sur les trois OS annoncés. La comparaison visuelle automatisée vérifie le titre de référence ; rendre les autres pages puis les archiver ne constitue pas une assertion sur leur lisibilité. `release.yml` n'attend pas toute la suite CI du même commit et `publish-github` dépend de `publish-pypi` : un blocage de registre peut bloquer les deux canaux.

## Positionnement et objectifs

Comparaison limitée aux présentations officielles consultées pendant l'audit, sans installer les concurrents ni comparer leur qualité sur des briefs identiques :

| Projet | Proposition observable | Conséquence pour Storyboard Studio |
| --- | --- | --- |
| [Presenton](https://github.com/presenton/presenton) | Génération IA généraliste, Docker/desktop, modèles multiples, import et PPTX éditable | « Local + éditable » ne suffit pas à différencier le projet. Mettre en avant la revue d'une décision, l'explicitation des sources et le fonctionnement sans modèle. |
| [Slidev](https://github.com/slidevjs/slidev) | Présentations destinées aux développeurs | Garder Markdown/Git comme intégration utile ; ne pas reconstruire un moteur de conférences web. |
| [PPTAgent](https://github.com/icip-cas/PPTAgent) | Génération PowerPoint agentique et démarche d'évaluation | S'inspirer des protocoles d'évaluation, sans présenter le benchmark structurel maison comme une victoire comparative. |
| Couche `python-pptx` déjà utilisée | Génération programmatique des objets Office | La valeur ajoutée à prouver est le workflow de décision et de revue au-dessus du moteur, pas l'existence du moteur lui-même. |

**Public prioritaire :** consultants, responsables produit/opérations et auteurs de briefs de décision sensibles. **Public contributeur :** développeurs Python, automatisation Office, local-first. Ne pas élargir avant d'avoir observé les usages.

Objectifs proposés, à mesurer et non à afficher comme acquis :

| Critère | Cible de sortie |
| --- | --- |
| Premier succès | Au moins 8/10 participants exportent le cas guidé sans aide en moins de 5 minutes après installation ; chronométrer séparément l'installation |
| Utilité | 10 sessions consenties et 5 briefs réels observés sans collecte du contenu ; publier les échecs et les faux positifs du Doctor |
| Réutilisation | Mesurer le second usage à 14–30 jours ; si absent, ajuster la proposition avant d'élargir les fonctionnalités |
| Robustesse | Aucun défaut P0 ouvert ; scénarios critiques P1 validés, 3/3 bundles de galerie vérifiables et régénérables |
| Installation | Parcours documenté réussi hors checkout sur chaque OS/architecture annoncé, sans Git ni Make pour l'utilisateur final |
| Fidélité | Tous les blocs publiés revus dans les viewers annoncés ; aucun contenu perdu ou tronqué silencieusement |
| Contributions | Issues actuelles reproductibles, réponse selon capacité déclarée, premier parcours contributeur testé ; aucun quota artificiel de PR/stars |

### Mode d'exécution

P0 = confiance, perte de données, intégrité ou obstacle de livraison. P1 = nécessaire à une version publiable et convaincante. P2 = amélioration guidée par les observations. Les durées ci-dessous sont des ordres de grandeur en jours de travail d'un mainteneur, pas des engagements ; prévoir plusieurs semaines pour les sessions, comptes et plateformes externes.

Chaque tâche possède un identifiant réutilisable dans une issue et n’est cochée qu’avec sa preuve. Les phases restent ouvertes tant que leurs critères requis manquent. Le couplage du test au nombre de cases a été retiré lors de 0.1, car le manifeste remplace la prose comme source de statut ; les autres travaux 5.2 restent à effectuer.

**Current gate:** la capacité de réponse aux **Discussions** n'est pas confirmée. La déclaration d'un responsable et de son rythme reste nécessaire ; aucune capacité n'est déduite de l'existence d'un fichier.

Cible initiale : **v0.3 — Workflow de décision vérifiable**, à numéroter précisément après revue des migrations. Une v1.0 n'est justifiée qu'après stabilisation des contrats et validation externe. Les capacités déjà codées ne nécessitent pas des releases fictives successives v0.4/v0.5.

Ordre : 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10. Des lectures et préparations peuvent se chevaucher, mais **la phase 10 ne démarre qu'après acceptation de toutes les phases 0 à 9**, publication et téléchargement de contrôle compris. Une correction produit découverte ensuite rouvre sa phase et invalide les prises concernées.

## Phase 0 — Réparer la promesse et les preuves existantes

- [x] Phase 0 acceptée localement le 8 septembre 2026 — intégrité et frontières de preuve corrigées ; la publication reste une phase ultérieure.

### 0.1 — Établir une frontière release/source/preuve

- [x] Tâche 0.1 validée : `docs/release-state.json` inventorie 12 promesses et leurs sources/tests/frontières de release ; le checker distingue workflow en pause, source présente, tag Git réel et publication non vérifiée. Politique et README mis à jour. `make lint format-check test launch-check` : 111 tests réussis ; contrôles négatifs de tag absent/divergent, arbre modifié, manifeste invalide et workflow seulement présent réussis. Les gates externes restent bloqués/non vérifiés, sans déclaration de publication.

**Objectif :** rendre impossible l'assimilation d'un fichier présent à une validation publique.

**Changements :** inventorier chaque promesse du README avec sa version d'introduction, son test et son statut distribué ; séparer dans la politique « prévu », « exécuté localement », « CI passée », « publié », « vérifié après téléchargement ». Ajouter un manifeste de preuves structuré versionné pour remplacer progressivement l'analyse de prose.

**Fichiers :** `README.md`, `CHANGELOG.md`, `docs/RELEASE_POLICY.md`, `docs/LAUNCH_KIT.md`, `storyboard_studio/launch.py`, futur manifeste sous `docs/`.

**Acceptation :** aucun SBOM, attestation, viewer ou package n'est déclaré publié sur la seule base de YAML ; un contrôle absent/en pause apparaît comme tel ; les fonctions non distribuées sont identifiées.

**Validation :** confronter manifeste, tag, package, assets GitHub et exécutions ; cas négatifs fichier présent/workflow absent, tag inexistant, version différente.

**Dépendances et risques :** aucune ; l'accès aux comptes peut rester non vérifié. Ne pas inventer un statut positif pour permettre une release.

### 0.2 — Stabiliser les reçus et réparer la galerie

- [x] Tâche 0.2 validée localement le 8 septembre 2026 : reçus v2, canonicalisation explicite, métadonnées recalculées, entrées invalides bornées ; 3/3 bundles actuels et 3/3 historiques vérifiés. `make lint format-check test` : 109 tests réussis ; smoke et validate-assets/site/layout/viewer-reports réussis. Les captures historiques restent identifiées ; aucun nouveau rendu Office revendiqué.

**Objectif :** faire fonctionner la preuve centrale sur les nouveaux documents et les documents historiques.

**Changements :** versionner la canonicalisation des données ; vérifier les documents anciens selon leur contrat sans appliquer silencieusement les nouveaux défauts ; expliciter le périmètre des hashes. Recalculer et comparer les champs dérivés du Doctor, de la couverture et de la provenance, ou les qualifier explicitement de non vérifiés. Traiter les JSON malformés sans traceback opaque. Régénérer les exemples actuels, tout en conservant des fixtures historiques pour tester la compatibilité.

**Fichiers :** `storyboard_studio/receipt.py`, `schemas.py`, `storyboard_studio/story.py`, `tests/test_receipt.py`, `tests/test_migrations.py` à créer si utile, `gallery/*`, `docs/MIGRATIONS.md`, `docs/EVIDENCE_WORKFLOW.md`.

**Acceptation :** 3/3 reçus de galerie valides avec le paquet candidat ; un ancien reçu légitime reste vérifiable selon sa version ; métadonnées incohérentes détectées ; un fichier modifié est rejeté. L'interface distingue intégrité interne, authenticité et véracité factuelle ; aucune signature implicite.

**Validation :** rejouer A4/A5, altération indépendante de chaque champ dérivé, chemins sortants, artefact absent, document ancien, ajout de valeurs par défaut, CLI et bundle HTTP.

**Dépendances et risques :** 0.1 ; migration sensible, éviter une acceptation permissive de tout ancien hash. Une régénération seule ne résout pas la régression de compatibilité.

## Phase 1 — Protéger fichiers, confidentialité et ressources

- [ ] Phase 1 acceptée — P0, estimation 4–6 jours.

### 1.1 — Isoler le stockage éphémère et appliquer l'expiration

- [x] Tâche 1.1 validée localement : cache dédié par utilisateur, marqueurs de propriété, écriture atomique, suppression des échecs partiels, TTL au téléchargement et sweep périodique. Les anciens fichiers `output/` ne sont jamais migrés/supprimés automatiquement. Tests de fichiers étrangers, symlinks, redémarrage, limite TTL, disque défaillant simulé et huit écritures concurrentes réussis. `make lint format-check test smoke` : 117 tests Python et smoke réussis ; `make browser-test` : 9 scénarios réussis. Le test de menu responsive attend son changement d'état au lieu d'une lecture instantanée sujette à course.

**Objectif :** aucun export durable ni fichier utilisateur supprimé par le serveur.

**Changements :** utiliser un répertoire éphémère dédié distinct des sorties CLI, identifier les fichiers possédés par le serveur, éviter les symlinks, écrire atomiquement et nettoyer les échecs partiels. Contrôler l'expiration au téléchargement et ajouter une purge périodique bornée. Expliquer que les téléchargements de l'utilisateur restent conservés.

**Fichiers :** `server.py`, `storyboard_studio/cli.py`, `tests/test_server.py`, `README.md`, `SECURITY.md`, `Dockerfile`.

**Acceptation :** A1 conserve le fichier étranger ; A3 refuse le téléchargement expiré ; PPTX/ZIP valides récents restent accessibles ; un répertoire imbriqué configurable fonctionne ; aucune purge des sorties CLI.

**Validation :** horloge simulée aux bornes TTL, noms étrangers et ressemblants, permissions, symlinks, disque plein simulé, exports concurrents et arrêt/redémarrage.

**Dépendances et risques :** phase 0 ; migration de l'ancien `output/` sans suppression opportuniste des fichiers déjà présents.

### 1.2 — Borner les requêtes et les appels réseau

- [x] Tâche 1.2 validée localement : middleware ASGI comptant les octets avant parsing, deadline de corps de 10 s, quatre requêtes modificatrices simultanées, Host/Origin contrôlés, limiteur de clients borné ; fournisseur local sans proxy/redirection et réponses limitées à 1 Mo ; SVG borné avant rasterisation. Suite complète : 126 tests Python réussis, smoke et validations assets/site/layout/rapports réussis ; 9 scénarios Chromium réussis. Les trois tests ASGI ciblés passent aussi, dont une nouvelle régression avec deux requêtes réellement concurrentes et récupération de capacité. Aucun appel à un modèle payant ni donnée privée utilisés.

**Objectif :** respecter la limite annoncée et la frontière « loopback-only ».

**Changements :** compter les octets ASGI avant parsing, y compris transfert segmenté ; borner export simultané, files d'attente et réponses de fournisseurs. Ajouter politique Host/Origin adaptée au service local et erreurs HTTP cohérentes. Auditer redirections et utilisation des proxies par l'adaptateur local, refuser toute sortie de boucle locale. Borner SVG avant allocation/rasterisation.

**Fichiers :** `server.py`, `storyboard_studio/providers.py`, `storyboard_studio/assets.py`, `tests/test_server.py`, `tests/test_providers.py`, `tests/test_assets.py`, `docs/PROVIDER_POLICY.md`.

**Acceptation :** A2 retourne 413 ; les petits payloads fonctionnent ; tentative de redirection non locale n'envoie pas le brief ; ressources et temps de traitement bornés ; UI conserve les données après 413/429/timeout.

**Validation :** corps sans longueur, longueur trompeuse, JSON invalide, requêtes concurrentes synthétiques, Host/Origin inattendus, serveur fournisseur simulé redirigeant, SVG aux dimensions extrêmes. Aucune donnée privée ni appel payant nécessaire.

**Dépendances et risques :** 1.1 ; ne pas casser les clients CLI/API locaux ni prétendre qu'un limiteur mémoire remplace une authentification multi-utilisateur.

### 1.3 — Assainir le contexte de distribution

- [ ] Implémentation locale validée le 8 septembre 2026 : contexte Docker restreint et utilisateur non-root configurés, wheel/sdist inspectés après insertion de sentinelles privées dans une copie temporaire, contrôleur d’archives et régressions ajoutés, contact privé concret publié. Audit des dépendances sans vulnérabilité connue après mise à jour de pip/pytest. Détails : `docs/SECURITY_VALIDATION.md`. Docker n’est pas installé ; Podman 5.2.5 est présent mais sa VM existante échoue au démarrage (`vfkit exited with code 1`) ; build, inspection et smoke du conteneur restent donc ouverts sur un runner fonctionnel.

**Objectif :** aucun contenu privé embarqué dans une image ou un paquet.

**Changements :** resserrer `.dockerignore` et les fichiers copiés ; exclure exports ZIP/JSON/receipts, environnements, clés, caches, recherches privées et rushes vidéo. Vérifier les dépendances natives Cairo et isoler le traitement SVG si nécessaire. Définir le mode Docker local avec port lié à `127.0.0.1`. Clarifier la politique de vulnérabilités et la version réellement maintenue.

**Fichiers :** `.dockerignore`, `Dockerfile`, `pyproject.toml`, `SECURITY.md`, `docs/INGESTION_THREAT_MODEL.md`, futur contrôle de contenu des distributions.

**Acceptation :** un fichier sentinelle synthétique dans `output/` n'apparaît ni dans l'image ni dans wheel/sdist ; conteneur non-root prêt et export fonctionnel ; voie de signalement privée utilisable ou contact concret publié.

**Validation :** inspection des archives et couches Docker, smoke sous utilisateur sans privilèges, audit de dépendances daté et scan de secrets sans afficher les valeurs.

**Dépendances et risques :** 1.1–1.2 ; Docker non testé pendant l'audit, dépendances natives à confirmer sur une image propre.

## Phase 2 — Permettre un vrai premier démarrage

- [ ] Phase 2 acceptée — P1, estimation 3–5 jours.

### 2.1 — Installer le studio complet hors du dépôt

- [ ] Implémentation locale : validateur réutilisable wheel/sdist dans deux venv indépendants et cwd vierges avec espaces/accents ; diagnostics port/cache et option `--open-browser` sans reloader. Documentation macOS/Linux/PowerShell ajoutée. Le parcours installé macOS ARM64/Python 3.14 est vérifié ; Windows/Linux et autres Python restent à exécuter avant acceptation multi-plateforme.

**Objectif :** l'auteur final n'a besoin ni de Git ni de Make.

**Changements :** tester wheel et sdist dans deux environnements vierges et un cwd vide ; vérifier ressources, schémas, tokens et CLI. Documenter PowerShell, macOS et Linux avec les chemins exacts. Ajouter un diagnostic de démarrage pour Python/dépendances natives, port occupé et dossier non inscriptible ; proposer ouverture du navigateur sans reloader de développement.

**Fichiers :** `pyproject.toml`, `storyboard_studio/resources.py`, `cli.py`, `start.sh`, `Makefile`, `README.md`, `docs/SUPPORT_MATRIX.md`, tests de package.

**Acceptation :** installation → `--version` → `demo --bundle` → `verify` → `serve` → export HTTP réussis depuis les artefacts sur chaque plateforme annoncée ; aucun recours aux fichiers du checkout ; erreurs compréhensibles.

**Validation :** wheel/sdist installés indépendamment ; chemins avec espaces/accents, port pris, utilisateur standard, lancement hors réseau après installation ; rapport OS/architecture/Python. Validation locale actuelle : base et extras `gemini,svg` sur macOS ARM64 / Python 3.14.6, avec bundle, reçu, studio HTTP, export PPTX et pack CSV régénéré vérifiés dans [`docs/installation-validation-2026-09-08.json`](docs/installation-validation-2026-09-08.json). Windows et Linux restent à exécuter.

**Dépendances et risques :** phases 0–1 ; `uvx` ne supprime ni la dépendance initiale au réseau ni celle à son propre outil. Ne promouvoir cette commande qu'après publication PyPI vérifiée en phase 9.

### 2.2 — Réduire le coût de la distribution

- [x] Validé localement : extras Gemini/SVG séparés, chargement Cairo différé, dépendances Pillow/Pydantic explicites, Uvicorn minimal, messages d’installation et fallback offline précis. Installations propres minimale wheel/sdist et wheel avec extras réussies ; imports paresseux contrôlés, SVG réellement rasterisé avec extra. Mesures avant/après et versions : `docs/DEPENDENCY_FOOTPRINT.md`. Les gates OS de 2.1 restent ouverts.

**Objectif :** installation sobre pour le parcours sans modèle.

**Changements :** mesurer taille, durée et dépendances installées ; évaluer un extra Gemini et un import paresseux CairoSVG plutôt que charger le SDK et Cairo pour toute commande ; déclarer explicitement les dépendances utilisées directement. Choisir un unique chemin utilisateur recommandé et garder les autres dans la documentation avancée.

**Fichiers :** `pyproject.toml`, `ai_helper.py`, `storyboard_studio/assets.py`, `providers.py`, `docs/PROVIDER_POLICY.md`, `README.md`.

**Acceptation :** fonctionnement offline de base conservé ; fournisseur/format optionnel manquant produit une instruction précise ; mesures avant/après publiées sans chiffres inventés.

**Validation :** installation minimale et installation avec extras, `.pptx` natif avec/sans image SVG, API/CLI/navigateur, absence d'import fournisseur au démarrage minimal.

**Dépendances et risques :** 2.1 ; migration de dépendances optionnelles à documenter, ne pas rendre inaccessible une capacité auparavant installée par défaut sans message clair.

## Phase 3 — Faire de l'éditeur un outil de travail

- [x] Phase 3 acceptée localement le 8 septembre 2026 — brief guidé révisable, sauvegarde/reprise explicite et assets portables validés dans les limites locales ; les essais humains et viewers Office restent leurs phases dédiées.

### 3.1 — Simplifier le brief et rendre le Doctor actionnable

- [x] Tâche 3.1 validée localement le 8 septembre 2026 : formulaire en trois sections, preuves facultatives repliables, listes >3 rejetées sans perte, extrait/owner sans label refusé explicitement ; troisième option conservée et portée de comparaison annoncée. Les textes de contexte/étape réutilisent davantage le brief. Navigation Doctor vers le champ/source concerné sans mutation implicite. La révision d’une story `decision-brief` recharge maintenant le formulaire guidé, conserve les options et les sources supplémentaires ; une modification d’extrait invalide honnêtement `author-checked` tout en gardant URL, licence et claim IDs. 171 tests Python et 15 scénarios navigateur passent, dont la création de brief depuis zéro, les limites de texte, la correction de finding et la recompilation avec métadonnées d’évidence. Contrôle visuel local du formulaire réalisé. Les observations d’utilisateurs restent la phase 6.

**Objectif :** montrer rapidement une décision compréhensible sans perdre les données importantes.

**Changements :** regrouper le brief en étapes courtes avec exemple local et aide contextuelle ; rendre les informations facultatives progressives. Remplacer les textes prescriptifs génériques du compilateur par des formulations issues du brief quand c'est possible sans invention. Expliciter la limite de comparaison à deux options ou supporter réellement la troisième. Donner à chaque finding un lien vers le champ concerné et distinguer problème bloquant, remarque et choix assumé.

**Fichiers :** `storyboard_studio/web/index.html`, `web/static/app.js`, `app.css`, `storyboard_studio/story.py`, `doctor.py`, `tests/test_story.py`, `tests/test_doctor.py`, `browser_tests/`.

**Acceptation :** brief créé de zéro sans le sample ; aucune option/contrainte perdue silencieusement ; correction d'un finding visible après nouvelle analyse ; zéro faux état « faits vérifiés » ; scénario clavier complet.

**Validation :** trois briefs synthétiques contrastés, valeurs limites, trois options, contexte long, pas de source, édition puis nouvelle compilation ; premiers essais utilisateurs repris en phase 6.

**Dépendances et risques :** phase 2 ; ne pas remplacer la saisie par du contenu fabriqué, ni confondre réduction du formulaire et suppression des informations nécessaires.

### 3.2 — Sauvegarder et reprendre sans ambiguïté

- [x] Validé localement : sauvegarde JSON explicite et confirmation de la version conservée, aucun stockage navigateur automatique, ouverture du projet depuis un onglet vierge, historique de story complète (sources/dispositions/thème), PPTX distinct de la sauvegarde, instantané protégé pendant export et analyse. 136 tests Python et douze parcours navigateur réussis ; régressions ciblées sur reprise, Undo/Redo, thème au clavier, export concurrent avec édition et refus HTTP 429. Documentation : `docs/SAVING_PROJECTS.md`. Les assets binaires restent un gate distinct de 3.3 ; les modifications non compilées du formulaire sont explicitement hors de la story sauvegardée.

**Objectif :** préserver le travail éditable et rendre le mode de conservation compréhensible.

**Changements :** séparer « export PPTX » de « sauvegarder le projet » ; tenir l'état de sauvegarde sur l'intégralité de la story, y compris sources et décisions du Doctor. Proposer une récupération locale opt-in avec effacement explicite, ou sauvegarde de projet explicite avec rappel clair ; garder le mode sans persistance. Harmoniser l'historique undo/redo et les états d'erreur ; protéger les changements pendant un export asynchrone.

**Fichiers :** `web/static/app.js`, `web/index.html`, `storyboard_studio/receipt.py`, `browser_tests/test_studio_browser.py`, documentation confidentialité.

**Acceptation :** après export PPTX, l'utilisateur sait si sa story est sauvegardée ; fermeture/réouverture ou import restaure les champs promis ; sources, ordre, dispositions et thèmes restent intacts ; annuler une opération n'annonce pas un succès.

**Validation :** refresh/crash simulé, export échoué, modification pendant export, undo/redo sur sources, imports invalides, purge locale choisie, plusieurs onglets ; zéro transmission réseau pour récupération.

**Dépendances et risques :** 0.2 et 3.1 ; la persistance locale peut conserver des briefs sensibles, donc pas d'activation implicite.

### 3.3 — Rendre les assets portables et accessibles

- [x] Validé localement : sélection CSV/JSON/PNG/JPEG/SVG avec hash, licence/attribution et description ; colonnes de graphique choisies explicitement ; ZIP portable avec manifeste, assets déclarés et variante sans entrées de preuve ; CLI `project pack/open` ; API sans dépendance au cwd et bornée (4 Mo d’assets, 8 Mo de requête projet/ZIP, 12 Mo décompressés). 161 tests Python réussis, treize scénarios navigateur réussis avec serveurs isolés ; parcours CSV + image → ZIP → nouvel onglet → PPTX vérifiant les valeurs natives 2/5/3 et l’image. Contrôle visuel effectué, dont colonnes masquées pour une image et absence de débordement à 320 px. Wheel et sdist installés hors dépôt : pack/open/régénération d’un vrai graphique CSV réussis. Tests ZIP hostiles, symlinks, empreintes altérées, limites, sources omises et SVG renforcé. Rapports : `docs/PORTABLE_PROJECTS.md`, `docs/portable-project-validation.json`. Aucune nouvelle validation Office ni publication revendiquée.

**Objectif :** créer puis régénérer un graphique ou une image sans connaître le cwd du serveur.

**Changements :** définir un projet local portable ; permettre sélection explicite CSV/JSON/PNG/JPEG/SVG autorisé, produire hash/métadonnées/alt/licence et valider côté serveur. Inclure dans le bundle les assets autorisés nécessaires à la régénération, avec manifeste et limites de taille ; conserver une variante sans sources privées. Nommer clairement les références externes non embarquées.

**Fichiers :** `storyboard_studio/assets.py`, `schemas.py`, `server.py`, `cli.py`, `receipt.py`, `web/`, `docs/REFERENCE_TEMPLATE_WORKFLOW.md`, tests assets/bundle.

**Acceptation :** un nouvel utilisateur crée un graphique depuis un CSV local et régénère son bundle dans un autre dossier ; aucun fichier récupéré implicitement ; dépendance manquante nommée ; licence/attribution conservées.

**Validation :** round-trip projet dans un cwd vide, archives hostiles/path traversal, symlinks, types falsifiés, limites pixels/octets, noms Unicode, empreinte modifiée, annulation import.

**Dépendances et risques :** phase 1 et 3.2 ; extension de surface d'ingestion à traiter comme un contrat borné, pas comme un import arbitraire de documents.

## Phase 4 — Garantir un résultat présentable et éditable

- [ ] Phase 4 acceptée — P1, estimation 4–7 jours.

### 4.1 — Unifier les règles d'export

- [ ] Avancement local : validation de schéma et préflight centralisés à l’entrée du renderer ; mêmes findings bloquants pour API simple/versionnée, bundles, projets portables, CLI et JSONL. Régression commune vérifiant refus et absence d’artefact/sidecar partiel ; la sauvegarde d’un projet à corriger reste possible. Validation : 164 tests Python, treize parcours navigateur, lint/format/smoke, build wheel/sdist inspecté et wheel installé hors dépôt avec régénération CSV réussis. Complément local : le compilateur conserve désormais les textes complets du brief ; séparation des limites de sauvegarde (2 000 caractères pour les champs concernés) et des limites de rendu, findings par chemin et navigation vers le champ. Régression de compilation, sauvegarde/réouverture ZIP et refus sans artefact sur textes longs ; 166 tests Python et 14 scénarios navigateur réussis (suite de 13 et nouveau scénario ciblé), lint/format réussis. Le renderer ne coupe plus les chaînes ni les retours à la ligne internes ; test PPTX des titres complets dans le pied de page et le panneau secondaire, des notes et du corps multiligne. Complément legacy : les projections comparison, metric, quote, chart/image et timeline conservent leurs détails ; les détails non typés sont affichés dans un panneau visible et le navigateur, avec budget `legacy_detail_characters`; les reçus historiques continuent d’utiliser la normalisation figée. Les tests de conservation, de timeline trop longue, de régression multi-projection, lint, suite Python complète (171 tests) et suite navigateur (15 scénarios) passent. Le contrôle visuel LibreOffice couvre maintenant les fixtures produit, typed blocks, native visuals et evidence, six palettes et toutes les pages listées dans `docs/viewer-reports/libreoffice-26.8.0.3-macos-26.0-2026-09-08.json`. Reste à obtenir une validation interactive Office et à prouver la conservation sur chaque entrée publique après la prochaine extraction de contrats.

**Objectif :** le même contenu reçoit les mêmes limites quel que soit le point d'entrée.

**Changements :** centraliser validation/preflight pour CLI, API, PPTX simple, bundle et outil JSONL ; définir explicitement blocage ou avertissement et un override traçable si nécessaire. Supprimer les troncatures silencieuses du compilateur/renderer au profit d'erreurs ou de transformations acceptées. Conserver le texte complet de la story.

**Fichiers :** `generate_pptx.py`, `storyboard_studio/layout.py`, `story.py`, `cli.py`, `tool_server.py`, `server.py`, `web/static/app.js`, tests layout/API/CLI.

**Acceptation :** A7 résolu ; aucun chemin ne contourne un défaut bloquant ; contenu, sources et ordre identiques entre story et export ; l'auteur comprend comment raccourcir/scinder.

**Validation :** mêmes fixtures à travers toutes les entrées, limites de texte, longueurs Unicode, citations multiples, thèmes, erreurs d'assets, rollback d'export.

**Dépendances et risques :** phases 0–3 ; ne pas exiger une absence de toute remarque narrative pour exporter une décision consciemment non résolue.

### 4.2 — Rapprocher le preview des objets finaux

- [ ] Avancement local ciblé : un rendu LibreOffice headless a reproduit deux chevauchements sur un titre long pourtant sous la limite de caractères. Hauteur de titre et position/taille du résumé corrigées dans les tokens embarqués et du checkout ; illustrations décoratives du panneau latéral retirées pour réserver la place au titre complet. Le cas a été rendu à nouveau et inspecté. Le rapport [LibreOffice 26.8.0.3 du 8 septembre 2026](docs/viewer-reports/libreoffice-26.8.0.3-macos-26.0-2026-09-08.json) couvre le produit, les huit blocs typés, les visuels natifs, les cas d’évidence, les cinq familles de pages et les six palettes ; six planches de contact archivées sont accompagnées de leurs SHA-256. 171 tests Python, 15 scénarios navigateur, lint/format et contrôles layout/assets réussissent. Ce contrôle local reste limité à LibreOffice headless : il ne valide ni toute l’édition interactive Office, ni PowerPoint, ni Keynote, ni Google Slides.

**Objectif :** aperçu utile à la composition et preuves réelles de qualité visuelle.

**Changements :** garder les tokens communs ; rendre graphiques, tables et images de façon représentative et isoler leurs contrôles d'édition ; hiérarchiser panneaux/diapositive active, réduire l'espace vide sans réécrire l'identité de marque. Regénérer toutes les fixtures avec le renderer candidat, vérifier chaque page et consigner les écarts de fonts/viewers.

**Fichiers :** `web/static/app.css`, `app.js`, `generate_pptx.py`, `storyboard_studio/layout.py`, `themes/`, `scripts/render_slides.py`, `scripts/compare_visual.py`, `docs/VIEWER_MATRIX.md`, `docs/viewer-reports/`, `docs/EXPORT_COMPATIBILITY.md`.

**Acceptation :** dix types de blocs revus, thèmes clair/sombre et six palettes contrôlées ; zéro clipping sur fixtures ; texte/table/chart sélectionnés et modifiés dans PowerPoint et LibreOffice sur la release candidate. Keynote/Google Slides restent « non vérifiés » sans test dédié.

**Validation :** captures bureau et 320/375 px, focus/clavier, zoom 200 %, reduced motion et lecteur d'écran ; rendus de toutes les diapositives, comparaison avec baseline du même viewer/version, test natif d'édition et réouverture. Ne pas remplacer cette preuve par l'inspection XML seule.

**Dépendances et risques :** 4.1 ; différences de fontes et de versions Office ; accès PowerPoint requis pour revendiquer sa compatibilité.

## Phase 5 — Renforcer l'architecture et la valeur des tests

- [ ] Phase 5 acceptée — P1, estimation 3–5 jours.

### 5.1 — Réduire la duplication des contrats

**Avancement local :** les contrats de story sont générés depuis
`storyboard_studio.schemas` (avec `schemas.py` comme shim de compatibilité)
vers les JSON versionnés et le renderer/preview utilisent le même layout
contract. Une première extraction à faible risque sépare maintenant les
validateurs de story, outline, blocs sémantiques, sources, assets et brand kits
dans `storyboard_studio/web/static/validation.js`; `app.js` leur fournit le
catalogue de thèmes et de blocs sans accès implicite au DOM ou au réseau. Le
parseur Markdown est maintenant canonique dans `storyboard_studio/markdown.py`
et `outline_markdown.py` conserve un shim de compatibilité. Le planificateur
fournisseur est canonique dans `storyboard_studio/ai_helper.py` et
`ai_helper.py` conserve lui aussi un shim ; les autres modules Python racine et
l'équivalence complète avec les modèles restent encore ouverts.

**Objectif :** rendre les corrections sûres et les contributions compréhensibles.

**Changements :** extraire progressivement état/historique, validation/import, rendu et appels API du `app.js` de 1 997 lignes ; organiser les renderers du fichier Python de 1 403 lignes par bloc seulement si cela simplifie les tests. Générer ou partager les contraintes plutôt que recopier les schémas en JS. Migrer les modules racine génériques vers le package avec adaptateurs de compatibilité. Ne pas imposer un framework ni une réécriture générale.

**Fichiers :** `web/static/app.js`, `web/static/validation.js`, `generate_pptx.py`, `schemas.py`, `server.py`, `storyboard_studio/markdown.py`, `outline_markdown.py`, `pyproject.toml`, `docs/ARCHITECTURE.md`, schémas sous `docs/schema/` et `storyboard_studio/data/`.

**Acceptation :** comportement public conservé ; imports packagés non ambigus ; mêmes corpus acceptés/rejetés par navigateur et backend ; pas de dépendance cachée au checkout.

La séparation navigateur est vérifiée par `node --check`, la suite Chromium
complète (15 scénarios) et les tests d'import/export existants. L'équivalence
exhaustive des corpus navigateur/backend et la migration des modules Python
racine doivent encore être prouvées avant de cocher la phase.

**Validation :** tests de caractérisation avant extraction, package hors dépôt, corpus de contrats invalides/valides, round-trip Markdown/JSON et snapshots de schémas.

**Dépendances et risques :** phases 0–4 ; petites extractions motivées par les changements précédents, pas de refonte esthétique du code.

### 5.2 — Tester les échecs qui invalident la promesse

**Avancement local :** les régressions des limites HTTP, du nettoyage d'exports,
des reçus historiques et actuels, des assets hostiles, des workflows de preuve,
des projections legacy et des rapports viewer sont désormais isolées dans des
fixtures/tests dédiés. Le test des rapports accepte plusieurs générations
archivées et sélectionne le candidat par date, sans compter les cases du
roadmap. `make test` : 175 tests Python (un avertissement Starlette/AnyIO).
La couverture de branches est maintenant mesurable avec `make coverage` (sans
seuil artificiel) et le rapport JSON est produit dans `output/coverage.json` :
le dernier run couvre 89 % des statements, 73 % des branches et 86 % au total
sur 175 tests (voir [`docs/COVERAGE.md`](docs/COVERAGE.md)). L'extraction des
contrats de 5.1 est encore ouverte.

Le rejet des redirections de l'adaptateur loopback ferme désormais explicitement
la réponse `HTTPError`, ce qui supprime le `ResourceWarning` produit par ce cas
de sécurité. Il reste seulement l'avertissement de dépréciation émis par la
version installée de Starlette/AnyIO ; sa correction dépend d'une combinaison de
dépendances compatible et n'est pas masquée par un filtre de test.

**Objectif :** les tests détectent les défauts A1–A10 et restent indépendants de la prose du roadmap.

**Changements :** utiliser des fixtures de statut pour `launch.py` ; remplacer l'assertion des onze cases par des tests de parsing et de décision sur données contrôlées. Ajouter vérification de la galerie, contrat de canonicalisation historique, pertes de données, limites et erreurs d'export. Mesurer la couverture des branches critiques pour repérer les trous, pas pour imposer un pourcentage décoratif.

**Fichiers :** `tests/test_launch.py`, `tests/test_receipt.py`, `tests/test_server.py`, `tests/test_assets.py`, `tests/test_site.py`, `browser_tests/`, `pyproject.toml`.

**Acceptation :** une modification normale du roadmap ne casse plus un test ; chaque défaut reproduit a un test qui échoue avant correction ; les scénarios continuent de couvrir le parcours réel ; aucune assertion ne nécessite un lancement bloqué pour toujours.

**Validation :** suites Python/Chromium, nouveaux corpus historiques, interruption/429/timeout, dépendances minimales, ordre de tests variable et tests isolés ; correction de l'avertissement Starlette/AnyIO selon compatibilité réelle.

**Dépendances et risques :** 5.1 ; pas de mocks qui masquent l'absence d'un téléchargement, d'une image ou d'un viewer réel.

## Phase 6 — Valider l'utilité et la prise en main

- [ ] Phase 6 acceptée — P1, 2–4 jours de préparation/analyse plus 2–4 semaines de recrutement et observations.

### 6.1 — Remplacer les preuves synthétiques par des observations consenties

**Objectif :** savoir si le produit aide à décider et si un nouvel utilisateur finit son travail.

**Changements :** appliquer le protocole existant à 10 personnes de la cible ; observer au moins cinq briefs réels sans collecter les contenus. Mesurer installation, premier export, compréhension du Doctor, correction, sources et réutilisation ; consigner abandons et faux positifs. Comparer qualitativement le processus habituel au résultat, sans expérience marketing fabriquée.

**Fichiers :** `docs/USER_RESEARCH_PROTOCOL.md`, `docs/USER_RESEARCH_STATUS.md`, `storyboard_studio/research.py`, futurs rapports agrégés anonymes.

**Acceptation :** 10 sessions et 5 workflows documentés avec consentement ; résultats positifs et négatifs publiés ; cible 8/10 premiers succès atteinte ou nouvelle itération produit puis retest ; aucune citation inventée.

**Validation :** validate/aggregate existants, revue des données anonymisées, distinction simulation/mainteneur/externe, suppression des données brutes selon consentement.

**Dépendances et risques :** phases 0–5 ; recrutement externe impossible à remplacer par des agents ou fixtures. Un échec de recrutement garde le jalon ouvert, sans allégation d'adoption.

### 6.2 — Choisir les améliorations utiles et le périmètre supporté

**Objectif :** éviter la croissance de fonctionnalités non demandées.

**Changements :** classer les frictions observées ; corriger les défauts bloquants et retester. Choisir un second template seulement si les données le justifient, sinon garder un seul parcours excellent. Réviser la comparaison concurrentielle et la cible à partir de l'usage ; adapter le benchmark à des échecs observés et anonymisés.

**Fichiers :** `docs/TEMPLATES.md`, `storyboard_studio/data/template-catalog.json`, `docs/COMPARISON.md`, `benchmarks/decision-v1/`, `docs/USER_RESEARCH_STATUS.md`.

**Acceptation :** décision de scope écrite et reliée à des observations ; benchmark reproductible avec limites déclarées ; aucune promesse d'avantage concurrentiel sans comparaison pertinente.

**Validation :** retest des frictions corrigées, benchmark de régression, revue des nouveaux templates/licences ; les corrections rouvrent leurs gates techniques.

**Dépendances et risques :** 6.1 ; pas d'obligation de nouveau template, de fournisseur ou de plateforme pour cocher la tâche.

## Phase 7 — Rendre l'automatisation exécutable et bloquante

- [ ] Phase 7 acceptée — P1, estimation 3–5 jours.

### 7.1 — Restaurer une CI compatible avec les contributions

**Avancement local :** `ci.yml`, `release.yml` et `review-story.yml` sont de
nouveau actifs sous `.github/workflows/`; les copies sous
`.github/workflows-disabled/` restent une référence d'audit. La configuration
conservée produit les checks Python/packaging/browser/benchmark et les preuves
de release sur Ubuntu. Le run CI `34212362981` du SHA `61f3d1b` est vert ; le
run du commit documentaire courant est observé séparément. La matrice OS
annoncée et l'édition des protections de branche ne sont pas prouvées
localement. Les actions `checkout@v7`, `setup-python@v7`,
`upload-artifact@v7` et `download-artifact@v7` sont résolues respectivement vers
`3d3c42e5aac5ba805825da76410c181273ba90b1`,
`5fda3b95a4ea91299a34e894583c3862153e4b97`,
`043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` et
`37930b1c2abaa49bbe596cd826c3c89aef350131`, dans les quatre fichiers actifs
et conservés. La nouvelle exécution de ce changement reste à observer.

**Objectif :** les contrôles requis se produisent réellement sur le commit proposé.

**Changements :** lors de l'exécution autorisée du roadmap, lever la pause volontaire en restaurant les fichiers conservés ; synchroniser les protections de branche avec les noms de jobs réels. Garder tests rapides sur PR ; ajouter clean-install OS/Python/architecture pertinente, smoke Docker et checks navigateur ; placer le rendu complet sur le gate de release. Épingler les actions sensibles par SHA et entretenir leurs mises à jour.

**Fichiers :** `.github/workflows-disabled/`, `.github/workflows/`, `.github/dependabot.yml`, `Makefile`, paramètres GitHub, `docs/MAINTAINER_PLAYBOOK.md`.

**Acceptation :** une PR non administrateur reçoit tous les checks requis ; pas de contrôle fantôme ; la release candidate passe Ubuntu/macOS/Windows pour le support revendiqué ; pause retirée du README seulement après une exécution vérifiée.

**Validation :** vraie exécution distante sur le SHA candidat, test PR externe sans secrets, permissions minimales, upload des rapports et de tous les rendus ; échec volontaire d'une fixture bloque le gate.

**Dépendances et risques :** phases 0–6 ; décision de réactivation nécessaire au moment de l'exécution si la pause est toujours souhaitée. Les pins de SHA et leur documentation sont un durcissement local ; ils ne prouvent ni l'exécution distante, ni la matrice OS, ni la protection de branche.

### 7.2 — Séparer build, release et lancement public

**Avancement local :** `launch.py` refuse les tags absents/divergents, les
workflows en pause, les rapports viewer invalides, les manifestes incomplets et
les publications non téléchargées ; les tests couvrent ces états contrôlés.
Le gate du dépôt reste bloqué tant qu'un tag, une distribution téléchargée,
les observations utilisateurs et la capacité mainteneur ne sont pas prouvés.

**Objectif :** une suite verte ou un tag fourni en argument ne suffit plus à déclarer le lancement prêt.

**Changements :** créer des gates structurés : candidat techniquement valide, package publié, contenu public vérifié, adoption documentée, communication prête. Faire dépendre la release des tests complets du SHA exact ; rendre les états manquants bloquants. Permettre un premier candidat sans exiger qu'il soit déjà publié sur PyPI, ni que la vidéo finale existe : ces contrôles appartiennent à des étapes ultérieures.

**Fichiers :** `storyboard_studio/launch.py`, `cli.py`, `tests/test_launch.py`, `.github/workflows/release.yml`, `docs/RELEASE_POLICY.md`, manifeste de preuves de 0.1.

**Acceptation :** aucun cercle « publier pour avoir le droit de publier » ; tag/version/SHA/artefacts réels concordent ; code de retour non nul sur échec du gate approprié ; les vieux MP4/rapports ne valident pas automatiquement une nouvelle version.

**Validation :** tag absent ou divergent, rapport périmé, CI en pause, registre absent, release partiellement publiée, réseaux indisponibles ; mode hors réseau explicitement incomplet.

**Dépendances et risques :** 7.1, 0.1, 5.2 ; éviter de coupler la disponibilité technique du paquet aux objectifs communautaires imprévisibles.

## Phase 8 — Préparer une présentation GitHub utile et une communauté soutenable

- [ ] Phase 8 acceptée — P1, estimation 3–5 jours.

### 8.1 — Recomposer README, documentation et vitrine

**Objectif :** comprendre la valeur en une lecture courte et obtenir un vrai résultat sans explorer des dizaines de documents.

**Changements :** placer promesse concrète, screenshot réel, installation recommandée et exemple téléchargeable en premier ; réduire le glossaire initial Doctor/Receipt. Déplacer l'API détaillée vers les docs existantes ; ajouter table d'orientation utilisateur/contributeur/intégrateur. Montrer trois cas régénérés et leurs limites. Distinguer la vitrine statique de l'application locale : `site/app.js` anime trois slides codées en dur, pas le moteur Python. Corriger les métadonnées « Live demo » si elles suggèrent un studio utilisable en ligne.

**Fichiers :** `README.md`, `docs/GALLERY.md`, `gallery/`, `docs/API.md`, `docs/SUPPORT_MATRIX.md`, `site/index.html`, `site/docs.html`, `site/app.js`, `site/llms.txt`, `pyproject.toml`.

**Acceptation :** utilisateur testeur trouve installation, limite locale, sortie et aide sans ambiguïté ; commandes copiées fonctionnent ; captures correspondent au candidat ; badge/version/lien exacts. L'ancienne vidéo est étiquetée historique jusqu'à son remplacement en phase 10.

**Validation :** liens locaux/externes, instructions testées depuis dossier vide, rendus README GitHub et site à 320/375/bureau, navigation clavier et contrastes, contrôle textes alternatifs ; aucun nouveau tournage à cette étape.

**Dépendances et risques :** phases 0–7 ; pas de simulation d'export public ni d'hébergement de briefs privés pour embellir la démo.

### 8.2 — Préparer contribution, support et partage

**Objectif :** convertir l'intérêt en essais et contributions utiles.

**Changements :** revoir les huit issues existantes plutôt qu'en créer des doublons ; préciser fichiers, durée indicative et reproduction. Tester le parcours CONTRIBUTING depuis un clone vierge ; nommer une capacité de réponse réaliste ; organiser Discussions sans inventer de retours. Préparer textes de lancement par public, artefacts à partager et méthode de bilan à 14/30 jours. Vérifier topics, description, homepage, image sociale et formulaires GitHub au moment de leur mise à jour.

**Fichiers :** `CONTRIBUTING.md`, `SUPPORT.md`, `docs/GOOD_FIRST_ISSUES.md`, `docs/MAINTAINER_PLAYBOOK.md`, `docs/LAUNCH_KIT.md`, `docs/LAUNCH_NOTES_*.md`, `.github/ISSUE_TEMPLATE/`, `docs/assets/social-preview.*`, réglages GitHub.

**Acceptation :** un contributeur peut reproduire une issue et lancer ses checks ; responsable et cadence explicités ; textes distinguent affiliations, fonctionnalités et preuves ; aucun message automatique de demande de star. La diffusion effective reste liée à la disponibilité du produit et de la vidéo finale.

**Validation :** revue du parcours sur clone propre, capacité déclarée, vérification des règles actuelles des destinations avant tout envoi, revue manuelle des textes/liens ; bilan basé sur essais, retours et usages répétés, sans télémétrie imposée.

**Dépendances et risques :** phase 6 ; maintien dans le temps et disponibilité humaine, pas seulement présence de fichiers communautaires.

## Phase 9 — Publier et vérifier les distributions finales

- [ ] Phase 9 acceptée — P1, estimation 4–8 jours, hors délais de comptes et signature.

### 9.1 — Livrer des artefacts adaptés à chaque public

**Avancement local :** wheel et sdist `0.2.0` ont été reconstruits depuis
`45959d4`. La validation de release locale accepte deux artefacts, leur
manifeste SHA-256 et un SBOM CycloneDX 1.5 (`output/release-evidence/`) ; la
validation de distribution confirme les ressources runtime et l’absence de
chemins privés. Cela ne constitue ni un tag, ni une publication GitHub/PyPI,
ni un binaire natif ou une provenance distante.

**Objectif :** téléchargement immédiatement utilisable et traçable.

**Changements :** mettre à jour version/changelog/migrations ensemble ; produire wheel et sdist du tag, checksums, SBOM et provenance. Configurer/vérifier Trusted Publishing sans token durable. Ajouter une voie sans Python pour le public auteur : choisir un lanceur packagé minimal ouvrant le studio local, puis produire des builds natifs par OS ciblé ; éviter une seconde interface desktop. Signer/notariser là où le canal le demande ; expliciter toute limite de signature plutôt que revendiquer une installation transparente. Si une plateforme ne peut pas être validée, la retirer du support annoncé avant gel du scope, avec justification.

**Fichiers :** `pyproject.toml`, `CHANGELOG.md`, `.github/workflows/release.yml`, futurs scripts/configurations sous `packaging/`, `scripts/generate_sbom.py`, `scripts/validate_release_evidence.py`, `docs/RELEASE_POLICY.md`, `README.md`.

**Acceptation :** pour chaque plateforme retenue, artefact de version exacte téléchargeable, installé sous compte standard et désinstallable ; l'app écoute localement ; `demo`, studio, export et reçu fonctionnent sans checkout. PyPI ne devient le chemin recommandé que lorsque son vrai paquet passe le même parcours. Ne pas qualifier un wheel `py3-none-any` de binaire natif.

**Validation :** machines/environnements propres pour wheel, sdist et chaque build ; Python absent pour le lanceur autonome ; OS/architecture/signature/poids mesurés ; assets embarqués présents ; antivirus/quarantaine et dépendances natives vérifiés sur la plateforme concernée.

**Dépendances et risques :** toutes phases 0–8 ; comptes PyPI, certificats, runners et maintenance multi-OS. Fixer une matrice réaliste ; ne pas télécharger d'énormes toolchains sans besoin mesuré.

### 9.2 — Vérifier la release publique avant le tournage

**Objectif :** la vidéo montrera exactement ce qu'un visiteur peut obtenir.

**Changements :** publier depuis les seuls artefacts validés, puis télécharger à nouveau depuis GitHub/PyPI. Vérifier hashes, version, schémas, signatures/attestations, installation et workflow complet. Publier la vitrine mise à jour et comparer les ressources servies au build prévu. Documenter reprise après échec partiel PyPI/GitHub ; ne pas déplacer ni écraser un ancien tag.

**Fichiers :** workflow release, `docs/RELEASE_POLICY.md`, `docs/VIEWER_MATRIX.md`, manifeste de preuves, `site/`, README et notes de release ; assets distants GitHub/PyPI.

**Acceptation :** liens publics accessibles, fichiers complets, provenance rattachée au tag, paquets installés après téléchargement, 3/3 galeries valides, rapports Office du candidat et CI du SHA exact ; pas de P0/P1 requis restant ouvert. La phase vidéo est encore ouverte et n'est pas présentée comme réalisée.

**Validation :** vérification indépendante des téléchargements et du lancement depuis dossier vide ; README/site rendus avec ressources réelles ; scénario d'échec partiel documenté ; fiche de gel précisant tag, SHA, environnements et limites.

**Dépendances et risques :** 9.1 ; OIDC, accès registre, service d'attestation et déploiement peuvent être des gates externes. Une publication incomplète bloque le tournage final ; aucun contournement documentaire.

## Phase 10 — Réaliser et vérifier la vraie vidéo du produit terminé

- [ ] Phase 10 acceptée — dernière phase, P1, estimation 2–4 jours après acceptation de toutes les phases précédentes.

**Condition impérative :** aucune capture de la nouvelle vidéo, aucun montage et aucun export final avant que les phases 0 à 9 soient implémentées et validées. La vidéo de 24,77 secondes déjà présente est un artefact historique ; elle ne satisfait pas cette phase. Utiliser obligatoirement la skill **`ffmpeg-video-editor`**, relire son `SKILL.md` lors de l'exécution, puis utiliser ses procédures de probe, montage, audio et encodage. L'audit en a lu les instructions, mais n'a produit aucune vidéo.

### 10.1 — Capturer une utilisation réelle de la version publiée

**Objectif :** démontrer le problème résolu et la chaîne complète avec des actions observables.

**Changements :** repartir du téléchargement public validé en 9.2, dans un environnement propre. Utiliser un brief synthétique explicitement identifié, mais une application réelle et des artefacts réellement générés. Scénario de 90–150 secondes à ajuster à la lisibilité : problème/choix et sources manquantes → installation ou démarrage réel → brief → compilation locale → finding du Doctor et correction → édition/comparaison et un visuel natif → sauvegarde projet/bundle → ouverture PPTX et édition de texte/table/chart dans un viewer validé → vérification du reçu. Ne pas montrer de fournisseur optionnel sans appel réellement validé et autorisé.

**Fichiers :** `scripts/record_demo.py` à adapter seulement maintenant, `docs/RELEASE_DEMO.md`, `docs/demo.md`, fixture sous `examples/briefs/`, rushes dans un répertoire temporaire hors Git.

**Acceptation :** actions, exports et résultat issus du même tag ; démarrage visible ; problème et bénéfice compréhensibles sans narration ; fenêtre de l'application et viewer réellement filmés ; pas de maquette, faux terminal, métrique inventée, fichier substitué ou assertion non montrée. Masquer par cadrage les autres fenêtres et secrets, ne pas capturer de contenu privé.

**Validation :** journal des prises avec version/SHA, environnement, commandes et hashes des sorties ; inspection des rushes via `ffprobe` avant montage ; répétition du parcours sans enregistrement ; vérifier que le recorder ne ferme pas une session Office préexistante et ne retombe jamais sur une capture globale non maîtrisée.

**Dépendances et risques :** toutes phases 0–9 ; droits de capture système, fenêtres modifiées, sortie différente du tag. Si un défaut produit apparaît, retour à sa phase puis nouvelle validation et nouvelles prises.

### 10.2 — Monter une démonstration sobre et lisible avec FFmpeg

**Objectif :** un montage professionnel dont chaque séquence conserve sa valeur de preuve.

**Changements :** employer `ffmpeg-video-editor` pour sélectionner les bonnes prises, couper les attentes, normaliser cadence/dimensions et concaténer proprement ; titres courts, zooms/recadrages motivés par les champs et résultats, transitions discrètes. Marquer toute accélération d'installation/export. Si voix : prise propre, nettoyage léger, normalisation en deux passes autour de −16 LUFS et crête ≤ −1,5 dBTP ; musique seulement avec licence et sans gêner. Une vidéo muette avec titres et transcription reste acceptable.

**Fichiers :** montage/script reproductible sous `scripts/`, `docs/demo.md`, sous-titres `.vtt`/`.srt`, `docs/assets/` pour livrables légers ; rushes et master lourd hors du dépôt.

**Acceptation :** lecture confortable, aucune coupe qui fait croire à une action réussie non filmée ; texte utile lisible ; titres exacts ; audio sans saturation ni variation gênante ; transcription fidèle et version visible.

**Validation :** lecture complète du montage, contrôle des points de coupe, comparaison avec les rushes et artefacts, analyse audio si piste présente, revue des licences. La sélection native d'un objet dans le viewer reste assez longue pour être comprise.

**Dépendances et risques :** 10.1 ; taille des textes lors du recadrage, son indisponible, transformations de vitesse qui faussent le temps annoncé.

### 10.3 — Exporter, publier et vérifier la lecture intégrale

**Objectif :** livrer une preuve vidéo réellement consultable depuis GitHub.

**Changements :** exporter un MP4 H.264, `yuv420p`, `+faststart`, 1920 × 1080 à 30 i/s ou 1280 × 720 si plus adapté au poids ; audio AAC si présent. Viser 90–150 secondes et ≤ 25 Mo pour la version principale, en adaptant compression/résolution sans sacrifier les textes. Produire si utile un extrait social réel de 20–40 secondes, cadré en 1:1 ou 9:16 sans couper l'information. Ajouter poster statique, durée et transcription ; intégrer la vraie vidéo ou un accès au lecteur GitHub avec commandes, jamais un GIF comme substitut du film complet.

**Fichiers :** `docs/assets/` ou assets de release/hébergement GitHub vérifié, `README.md`, `site/index.html`, `docs/demo.md`, `docs/RELEASE_DEMO.md`, futur rapport vidéo contenant hashes et caractéristiques.

**Acceptation :** vidéo principale disponible depuis README et release/site ; lecture complète, pause et déplacement dans la vidéo fonctionnent ; codec, durée, résolution, cadence, poids et audio consignés ; aucune ressource 404 ni simple lien brut donnant l'impression d'un lecteur intégré. Vérifier le comportement réel du README GitHub, ne pas supposer que toute balise HTML vidéo y fonctionne.

**Validation :** `ffprobe -v error -show_streams -show_format -of json <final.mp4>` ; décodage intégral `ffmpeg -v error -i <final.mp4> -f null -` ; lecture humaine du début à la fin dans au moins deux navigateurs, puis lecture complète après téléchargement du fichier publié et depuis le parcours README. Vérifier synchronisation, frames noires/gelées, lisibilité, poster et sous-titres. Calculer SHA-256 et comparer fichier local/téléchargé. La réussite de FFmpeg seule ne valide pas la lecture dans GitHub.

**Dépendances et risques :** 10.2 et stabilité du tag gelé ; limites actuelles de l'hébergement à vérifier au moment de l'upload. Toute correction produit rouvre les validations concernées avant remplacement des prises. Clôturer cette dernière phase seulement lorsque le film montre le produit final fonctionnel et que ses fichiers publiés ont été intégralement vérifiés.
