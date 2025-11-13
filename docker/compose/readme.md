  163  cd docker
  164  cd compose
  165  docker compose logs -f mios-orig-1
  166  docker compose logs -f mios_orig_1
  167  docker compose logs -f mios_orig
  168  docker compose logs -f mios_orig --tail 100
  169  docker compose logs -f mios_orig --tail 100 > test.log
  170  history
