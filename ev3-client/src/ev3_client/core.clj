(ns ev3-client.core
  (:require [ev3-client.robot :refer [connect turn fw]])
  (:gen-class))

(defn -main
  "I don't do a whole lot ... yet."
  [& args]
  (println "Hello, World!"))

(connect)

(do 
  (fw 1)
  (turn :right)
  (fw 1)
  (turn :right)
  (fw 1)
  (turn :right)
  (fw 1)
  (turn :right)

  )


(turn :right )
