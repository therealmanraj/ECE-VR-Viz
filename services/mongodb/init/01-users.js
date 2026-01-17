// Creates a DB + user Trino can use.
// NOTE: Trino needs WRITE access to the schema collection (_schema by default). :contentReference[oaicite:1]{index=1}

db = db.getSiblingDB("ece");

db.createUser({
  user: "trino",
  pwd: "trino_password_dev",
  roles: [
    { role: "readWrite", db: "ece" }, // simplest for dev
  ],
});
